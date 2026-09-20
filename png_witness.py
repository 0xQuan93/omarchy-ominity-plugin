"""Validate the bounded, non-interlaced PNG witnesses Ominity stores."""

from __future__ import annotations

import struct
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_DECODED_BYTES = 128 * 1024**2
SAMPLES = {2: 3, 6: 4}


def png_dimensions(contents: bytes) -> tuple[int, int]:
    """Check PNG chunks, image stream, and the canonical 7:12 canvas."""
    if not isinstance(contents, bytes) or not contents.startswith(SIGNATURE):
        raise ValueError("Ominity visual witness is not a PNG")
    cursor = len(SIGNATURE)
    width = height = bit_depth = color_type = None
    row_bytes = None
    image_data = []
    saw_idat = saw_iend = image_closed = False
    while cursor + 12 <= len(contents):
        size = struct.unpack_from(">I", contents, cursor)[0]
        chunk_type = contents[cursor + 4:cursor + 8]
        end = cursor + 12 + size
        if end > len(contents) or not all(65 <= c <= 90 or 97 <= c <= 122 for c in chunk_type):
            raise ValueError("Malformed Ominity PNG chunk")
        data = contents[cursor + 8:cursor + 8 + size]
        crc = struct.unpack_from(">I", contents, end - 4)[0]
        if zlib.crc32(chunk_type + data) != crc:
            raise ValueError("Ominity PNG chunk has invalid CRC")
        if cursor == len(SIGNATURE) and chunk_type != b"IHDR":
            raise ValueError("Ominity PNG lacks IHDR")
        if chunk_type == b"IHDR":
            if width is not None or size != 13:
                raise ValueError("Invalid Ominity PNG IHDR")
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", data)
            if (width < 1 or height < 1 or width * 12 != height * 7
                    or color_type not in SAMPLES or bit_depth != 8
                    or compression != 0 or filtering != 0 or interlace != 0):
                raise ValueError("Ominity visual witness must be a non-interlaced 7:12 PNG")
            row_bytes = (width * SAMPLES[color_type] * bit_depth + 7) // 8
            if height * (row_bytes + 1) > MAX_DECODED_BYTES:
                raise ValueError("Ominity PNG decoded image exceeds size limit")
        elif chunk_type == b"IDAT":
            if width is None or saw_iend or image_closed:
                raise ValueError("Invalid Ominity PNG image stream")
            saw_idat = True
            image_data.append(data)
        elif chunk_type == b"IEND":
            if size != 0 or not saw_idat or end != len(contents):
                raise ValueError("Invalid Ominity PNG end marker")
            saw_iend = True
            break
        elif chunk_type == b"PLTE":
            raise ValueError("Ominity PNG witnesses do not use palettes")
        elif chunk_type[:1].isupper():
            raise ValueError("Unsupported Ominity PNG critical chunk")
        if saw_idat and chunk_type != b"IDAT":
            image_closed = True
        cursor = end
    if not saw_iend:
        raise ValueError("Incomplete Ominity PNG")
    expected = height * (row_bytes + 1)
    decoder = zlib.decompressobj()
    try:
        pixels = decoder.decompress(b"".join(image_data), expected + 1)
        if len(pixels) > expected:
            raise ValueError("Ominity PNG image data exceeds canvas")
        pixels += decoder.flush(expected + 1 - len(pixels))
    except zlib.error as error:
        raise ValueError("Invalid Ominity PNG image stream") from error
    if (len(pixels) != expected or not decoder.eof or decoder.unused_data
            or decoder.unconsumed_tail
            or any(pixels[row * (row_bytes + 1)] > 4 for row in range(height))):
        raise ValueError("Invalid Ominity PNG image data")
    return width, height
