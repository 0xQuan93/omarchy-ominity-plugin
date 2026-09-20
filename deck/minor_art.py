"""Original, palette-aware pictorial plates for Ominity's Minor Arcana.

The four suits inhabit different worlds. Each rank changes the action in that
world, so the objects in the picture serve the reading rather than a pip grid.
All geometry is SVG that QtSvg can render sharply at any desktop scale.
"""

from __future__ import annotations


def _mix(first: str, second: str, amount: float) -> str:
    a = tuple(int(first[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(second[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x * (1 - amount) + y * amount):02x}" for x, y in zip(a, b))


def _path(d: str, fill: str = "none", stroke: str = "none", width: float = 1.4,
          opacity: float = 1, extra: str = "") -> str:
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round" opacity="{opacity}" {extra}/>')


def _circle(x: float, y: float, r: float, fill: str, stroke: str = "none",
            width: float = 1.4, opacity: float = 1) -> str:
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{width}" opacity="{opacity}"/>')


def _ellipse(x: float, y: float, rx: float, ry: float, fill: str,
             stroke: str = "none", width: float = 1.4) -> str:
    return (f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}"/>')


def _group(x: float, y: float, scale: float, body: str, rotate: float = 0) -> str:
    return f'<g transform="translate({x} {y}) rotate({rotate}) scale({scale})">{body}</g>'


class _Colors:
    def __init__(self, palette, suit: str):
        self.paper = palette.paper
        self.ink = palette.ink
        self.gold = palette.gold
        self.accent = palette.accents[suit]
        self.pale = _mix(self.paper, self.accent, .16)
        self.mid = _mix(self.paper, self.accent, .36)
        self.warm = _mix(self.paper, self.gold, .32)
        self.deep = _mix(self.paper, self.ink, .72)
        self.quiet = _mix(self.paper, self.ink, .27)
        self.light = _mix(self.paper, self.gold, .1)


def _rays(x: int, y: int, c: _Colors, count: int = 16, length: int = 84) -> str:
    lines = []
    for i in range(count):
        angle = i * 360 / count
        lines.append(_path(f"M{x} {y - 34}L{x} {y - length}", stroke=c.gold,
                           width=1.1, opacity=.65,
                           extra=f'transform="rotate({angle} {x} {y})"'))
    return "".join(lines)


def _spark(x: float, y: float, r: float, c: _Colors) -> str:
    return _path(f"M{x} {y-r}L{x+r*.18} {y-r*.18}L{x+r} {y}L{x+r*.18} {y+r*.18}"
                 f"L{x} {y+r}L{x-r*.18} {y+r*.18}L{x-r} {y}L{x-r*.18} {y-r*.18}Z",
                 c.gold, c.paper, .7)


def _wand(x: float, y: float, scale: float, c: _Colors, rotation: float = 0,
          flame: bool = False) -> str:
    body = (_path("M-3 29L-2 -32Q0 -38 3 -32L3 29Z", c.deep, c.gold, 1.5)
            + _path("M-2 -13Q-14 -27 -22 -24M3 3Q15 -12 21 -10M-1 13Q-10 2 -18 4",
                    stroke=c.accent, width=2)
            + _path("M-22 -24Q-16 -28 -14 -27M21 -10Q15 -17 15 -12M-18 4Q-13 0 -10 2",
                    fill=c.accent))
    if flame:
        body += _path("M0 -35Q-12 -51 -1 -65Q3 -56 7 -53Q15 -42 0 -35Z", c.gold, c.ink, 1.1)
        body += _path("M0 -40Q-4 -48 0 -55Q7 -47 0 -40Z", c.paper)
    return _group(x, y, scale, body, rotation)


def _cup(x: float, y: float, scale: float, c: _Colors, full: bool = True) -> str:
    body = (_path("M-19 -24Q-18 -2 -9 4Q0 11 9 4Q18 -2 19 -24Z", c.warm, c.ink, 1.6)
            + _ellipse(0, -24, 19, 4, c.paper, c.gold, 1.3)
            + _path("M0 9V25M-13 26H13", stroke=c.ink, width=1.8)
            + _path("M-20 -13Q-31 -17 -27 -6Q-25 1 -16 -2M20 -13Q31 -17 27 -6Q25 1 16 -2",
                    stroke=c.gold, width=1.2))
    if full:
        body += _path("M-14 -24Q0 -27 14 -24", stroke=c.accent, width=2.2)
    return _group(x, y, scale, body)


def _sword(x: float, y: float, scale: float, c: _Colors, rotation: float = 0) -> str:
    body = (_path("M0 -43L5 8L0 14L-5 8Z", c.paper, c.ink, 1.5)
            + _path("M0 -38V9", stroke=c.accent, width=1)
            + _path("M-17 15Q0 12 17 15L13 19H-13Z", c.gold, c.ink, 1.1)
            + _path("M0 19V33", stroke=c.ink, width=3)
            + _circle(0, 34, 3, c.gold, c.ink, 1))
    return _group(x, y, scale, body, rotation)


def _coin(x: float, y: float, radius: float, c: _Colors, feature: bool = True) -> str:
    body = _circle(x, y, radius, c.warm, c.gold, 2)
    body += _circle(x, y, radius * .77, "none", c.ink, 1.1)
    if feature:
        points = [(0, -1), (.59, .81), (-.95, -.31), (.95, -.31), (-.59, .81), (0, -1)]
        d = "M" + "L".join(f"{x + px * radius * .66:.1f} {y + py * radius * .66:.1f}"
                         for px, py in points)
        body += _path(d, stroke=c.accent, width=1.3)
    else:
        body += _circle(x, y, radius * .27, c.accent)
    return body


def _person(x: float, y: float, scale: float, c: _Colors, pose: str = "standing",
            facing: int = 1, cloak: str | None = None) -> str:
    """Faceted human silhouettes with a few readable gestures, not stock icons."""
    garment = cloak or c.deep
    head = (_circle(0, -64, 8.3, c.paper, c.ink, 1.5)
            + _path("M-9 -66Q-8 -79 1 -78Q12 -77 10 -64Q6 -70 0 -69Q-6 -68 -9 -66Z",
                    c.ink))
    if pose == "sitting":
        form = (_path("M-9 -55Q0 -61 10 -55L19 -19L8 -8L-17 -10L-22 -30Z",
                      garment, c.ink, 1.5)
                + _path("M-18 -13Q5 -20 20 -6L34 -4M-17 -12L-29 0", stroke=c.ink, width=5)
                + _path("M-9 -50L-19 -25L-6 -18M8 -49L21 -31L28 -27",
                        stroke=c.paper, width=3.5))
    elif pose == "kneel":
        form = (_path("M-10 -55Q1 -62 13 -54L18 -25L-3 -15L-21 -29Z", garment, c.ink, 1.5)
                + _path("M-7 -17L-24 -8L-31 0M9 -16L25 -7L12 1", stroke=c.ink, width=5)
                + _path("M-9 -49L-19 -22L-28 -11M10 -48L22 -23L29 -12",
                        stroke=c.paper, width=3.5))
    elif pose == "fallen":
        form = (_path("M-11 -55Q0 -61 10 -56L19 -24L-11 -20L-22 -40Z", garment, c.ink, 1.5)
                + _path("M-16 -22L-22 -1M11 -22L21 0", stroke=c.ink, width=5)
                + _path("M-12 -49L-26 -25M9 -49L23 -32", stroke=c.ink, width=4))
    else:
        form = (_path("M-13 -55Q0 -61 13 -55L19 -17L13 2H-13L-19 -17Z",
                      garment, c.ink, 1.5)
                + _path("M-8 -9L-10 5M9 -9L12 5", stroke=c.ink, width=5)
                + _path("M-12 -48L-25 -22L-28 -11M12 -48L24 -23L29 -10",
                        stroke=c.ink, width=4)
                + _path("M-11 -42Q0 -35 11 -42M0 -38V-7", stroke=c.gold, width=1.1))
    return f'<g transform="translate({x} {y}) scale({scale * facing} {scale})">{head}{form}</g>'


def _horse(x: float, y: float, scale: float, c: _Colors, moving: bool = False) -> str:
    legs = ("M-27 -5L-36 20M-9 -4L-4 20M18 -5L10 21M30 -7L40 18" if not moving
            else "M-27 -5L-44 15M-9 -4L-20 21M18 -5L30 15M30 -7L51 10")
    body = (_path("M-40 -19Q-21 -32 15 -25L34 -38L44 -29L39 -10L29 -2Q7 3 -23 -2L-35 -5Z",
                  c.mid, c.ink, 1.8)
            + _path("M29 -34L32 -49L44 -45L47 -27M-40 -20Q-55 -35 -51 -9",
                    stroke=c.ink, width=2.3)
            + _path(legs, stroke=c.ink, width=4)
            + _circle(39, -33, 1.8, c.ink)
            + _path("M-18 -25Q-6 -32 8 -29", stroke=c.gold, width=1.7))
    return _group(x, y, scale, body)


def _tree(x: float, y: float, scale: float, c: _Colors, flowering: bool = False) -> str:
    body = (_path("M-4 0Q-3 -36 -8 -56M2 -35Q17 -52 28 -52M-3 -49Q-18 -68 -30 -67",
                  stroke=c.ink, width=5)
            + _path("M-33 -66Q-36 -88 -15 -91Q-6 -106 10 -93Q26 -99 34 -82Q41 -67 26 -57Q11 -48 -1 -58Q-17 -51 -33 -66Z",
                    c.mid, c.accent, 1.8)
            + _path("M-29 -75Q-9 -68 0 -79M4 -87Q20 -80 27 -70", stroke=c.gold, width=1.2))
    if flowering:
        body += "".join(_spark(px, py, 4, c) for px, py in ((-23, -76), (5, -87), (24, -67)))
    return _group(x, y, scale, body)


def _architecture(c: _Colors, suit: str, number: int) -> str:
    """A quiet suit-specific printmaker's aperture behind the active scene."""
    rise = (number % 3) * 7
    if suit == "Wands":
        return (_path(f"M39 365V{191+rise}L82 {151+rise}L140 {173+rise}"
                      f"L198 {151+rise}L241 {191+rise}V365",
                      stroke=c.gold, width=1.2, opacity=.56)
                + _path(f"M52 365V{201+rise}L87 {167+rise}L140 {188+rise}"
                        f"L193 {167+rise}L228 {201+rise}V365", stroke=c.accent,
                        width=1.1, opacity=.44)
                + _path("M40 365H240", stroke=c.ink, width=1.3))
    if suit == "Cups":
        return (_path(f"M38 365V{189+rise}Q80 {143+rise} 140 {166+rise}"
                      f"Q202 {143+rise} 242 {189+rise}V365", stroke=c.gold,
                      width=1.2, opacity=.58)
                + _path(f"M52 365V{198+rise}Q89 {161+rise} 140 {182+rise}"
                        f"Q190 {161+rise} 228 {198+rise}V365", stroke=c.accent,
                        width=1.1, opacity=.44)
                + _path("M40 365H240", stroke=c.ink, width=1.3))
    if suit == "Swords":
        return (_path(f"M39 365V{197+rise}L140 {139+rise}L241 {197+rise}V365",
                      stroke=c.gold, width=1.2, opacity=.6)
                + _path(f"M51 365V{207+rise}L140 {157+rise}L229 {207+rise}V365",
                        stroke=c.accent, width=1.1, opacity=.43)
                + _path("M40 365H240", stroke=c.ink, width=1.3))
    return (_path(f"M39 365V{184+rise}Q140 {105+rise} 241 {184+rise}V365",
                  stroke=c.gold, width=1.2, opacity=.58)
            + _path(f"M52 365V{192+rise}Q140 {128+rise} 228 {192+rise}V365",
                    stroke=c.accent, width=1.1, opacity=.45)
            + _path("M40 365H240", stroke=c.ink, width=1.3))


def _world(c: _Colors, suit: str, n: int) -> str:
    """Atmospheric depth and changing light, with a visual dialect per suit."""
    shift = (n * 7) % 32
    if suit == "Wands":
        sun_x = 185 + (n % 3) * 14
        return (_path("M24 79H256V388H24Z", c.light)
                + _rays(sun_x, 162, c, 18, 120)
                + _circle(sun_x, 162, 32, c.warm, c.gold, 1.4)
                + _path(f"M24 {278+shift}L66 {220+shift}L98 {254+shift}L151 {194+shift}"
                        f"L211 {259+shift}L256 {222+shift}V388H24Z", c.pale, c.accent, 1.1, .7)
                + _path("M24 338Q83 291 123 335Q178 289 256 331V388H24Z", c.mid,
                        c.accent, 1.6)
                + _path("M30 353Q86 329 118 350M161 347Q207 317 249 349",
                        stroke=c.gold, width=1, opacity=.65))
    if suit == "Cups":
        moon_x = 184 - (n % 3) * 14
        return (_path("M24 79H256V388H24Z", c.pale)
                + _circle(moon_x, 156, 34, c.warm, c.gold, 1.4)
                + _circle(moon_x + 13, 146, 30, c.pale)
                + _path("M24 283Q68 253 103 282Q153 247 189 281Q224 252 256 279V388H24Z",
                        c.mid, c.accent, 1.4, .68)
                + _path("M24 320Q78 304 135 321Q191 306 256 320V388H24Z",
                        c.pale, c.accent, 1.6)
                + "".join(_path(f"M28 {333+i*13}Q61 {325+i*13} 92 {333+i*13}T157 {333+i*13}"
                                 f"T249 {333+i*13}", stroke=c.accent, width=1.25,
                                 opacity=.65 - i*.1) for i in range(4))
                + _path(f"M{moon_x-12} 311L{moon_x+12} 311M{moon_x-18} 331L{moon_x+18} 331",
                        stroke=c.gold, width=1.5, opacity=.7))
    if suit == "Swords":
        return (_path("M24 79H256V388H24Z", c.light)
                + _path("M40 86L40 315M76 86L76 288M112 86L112 308M148 86L148 290"
                        "M184 86L184 304M220 86L220 289", stroke=c.accent, width=1, opacity=.23)
                + _path("M24 183Q58 165 87 181T151 178T256 183M24 223Q71 210 105 221"
                        "T188 215T256 220", stroke=c.ink, width=1.1, opacity=.3)
                + _path(f"M24 {331+shift//2}L72 {294+shift//2}L117 {319+shift//2}"
                        f"L164 {279+shift//2}L207 {315+shift//2}L256 {291+shift//2}V388H24Z",
                        c.pale, c.accent, 1.25)
                + _path("M24 360Q76 326 134 349Q201 312 256 350V388H24Z",
                        c.mid, c.ink, 1.2, .55)
                + _path("M52 128L83 119M103 144L142 133M178 113L222 99",
                        stroke=c.accent, width=1.8, opacity=.7))
    return (_path("M24 79H256V388H24Z", c.light)
            + _circle(194, 155, 27, c.warm, c.gold, 1.2)
            + _path("M24 303Q77 242 121 289Q164 243 256 291V388H24Z",
                    c.pale, c.accent, 1.3, .72)
            + _path("M24 347Q80 293 126 335Q194 286 256 335V388H24Z",
                    c.mid, c.ink, 1.2, .56)
            + "".join(_path(f"M{x} 366V{271+(x%4)*8}M{x} {291+(x%4)*8}Q{x-9} {282+(x%4)*8} {x-16} {289+(x%4)*8}"
                             f"M{x} {302+(x%4)*8}Q{x+8} {289+(x%4)*8} {x+17} {296+(x%4)*8}",
                             stroke=c.accent, width=1.4, opacity=.54)
                    for x in (54, 226))
            + _path("M24 367H256", stroke=c.gold, width=1.2, opacity=.65))


def _wands(n: int, c: _Colors) -> str:
    w = lambda x, y, s=1, a=0, f=False: _wand(x, y, s, c, a, f)
    p = lambda x, y, s=1, pose="standing", face=1, cloak=None: _person(x, y, s, c, pose, face, cloak)
    if n == 1:
        return (_path("M38 296Q71 268 95 274L129 251L148 261L118 280L84 303L41 320Z",
                      c.paper, c.ink, 2.4)
                + w(146, 221, 2.2, -12, True)
                + _path("M91 272Q110 253 135 247M71 297Q89 292 101 285",
                        stroke=c.gold, width=1.5)
                + _spark(201, 226, 7, c) + _spark(82, 183, 5, c))
    if n == 2:
        return (_path("M38 309H242V337H38ZM54 274H226V309H54Z", c.deep, c.ink, 2)
                + _path("M75 275V210M205 275V209", stroke=c.gold, width=2)
                + w(75, 242, 1.2) + w(205, 242, 1.2)
                + p(140, 294, 1.15) + _circle(166, 237, 15, c.warm, c.gold, 1.4)
                + _path("M166 222V252M151 237H181", stroke=c.gold, width=1)
                + _path("M141 276L182 228", stroke=c.paper, width=2.4))
    if n == 3:
        ships = "".join(_path(f"M{x-18} {y}H{x+18}L{x+8} {y+10}H{x-10}Z", c.deep,
                                  c.ink, 1.2) + _path(f"M{x} {y-26}V{y}L{x+16} {y-4}Z",
                                                       c.paper, c.gold, 1.1)
                        for x, y in ((92, 293), (175, 307)))
        return (ships + _path("M31 350Q99 313 144 345T256 342", stroke=c.ink, width=1.4)
                + p(185, 338, 1.15, face=-1) + w(112, 308, 1.2) + w(153, 320, 1)
                + w(214, 313, 1.1))
    if n == 4:
        posts = "".join(w(x, 295, 1.4) for x in (63, 106, 174, 217))
        return (_path("M60 219Q140 168 220 219M61 226Q140 188 219 226",
                      stroke=c.gold, width=3)
                + _path("M61 220Q73 246 91 222Q107 239 122 211Q143 228 158 211"
                        "Q180 239 198 220Q210 238 220 220", stroke=c.accent, width=3)
                + posts + p(119, 359, .77) + p(163, 359, .77, face=-1)
                + _path("M112 322Q140 303 169 322", stroke=c.gold, width=2)
                + _spark(139, 190, 8, c))
    if n == 5:
        sticks = "".join(w(x, y, 1.5, a) for x, y, a in ((88, 268, 55),
                            (190, 265, -55), (120, 222, -25), (164, 230, 27), (140, 300, 85)))
        return (_circle(140, 256, 75, "none", c.gold, 1.1, .7)
                + _path("M98 249Q136 216 180 243Q188 271 155 289Q119 302 97 270Z",
                        c.mid, c.accent, 1.4, .62)
                + sticks
                + _path("M47 282L86 262L95 272L58 295M226 286L192 265L181 275L216 301",
                        c.paper, c.ink, 1.8)
                + _path("M116 344L127 299L140 303L135 350M161 346L157 307L170 300L179 345",
                        c.paper, c.ink, 1.6)
                + "".join(_spark(x, y, 5, c) for x, y in ((128, 240), (153, 264), (106, 279), (184, 223)))
                + _path("M44 350Q140 320 239 350", stroke=c.gold, width=1.5))
    if n == 6:
        return (_horse(137, 338, 1.35, c, True) + p(131, 292, .87)
                + w(130, 216, 1.2) + _path("M105 181Q128 164 153 181Q146 198 129 199Q111 198 105 181Z",
                                           c.mid, c.gold, 1.7)
                + "".join(_spark(x, y, 4, c) for x, y in ((80, 300), (202, 299), (70, 256), (215, 264)))
                + _path("M43 335Q62 301 76 335M204 335Q222 305 241 335",
                        stroke=c.ink, width=2))
    if n == 7:
        return (_path("M24 357L133 269L256 357V388H24Z", c.deep, c.ink, 2)
                + p(140, 278, 1.16) + w(140, 238, 1.3, -22)
                + "".join(w(x, 346, .83, a) for x, a in ((48, -25), (79, 12), (105, -8),
                                                           (180, 17), (210, -12), (238, 25)))
                + _path("M89 284L140 276L190 292", stroke=c.gold, width=1.6))
    if n == 8:
        return (_path("M26 360Q140 335 255 358", stroke=c.ink, width=1.5)
                + "".join(w(75 + i * 25, 215 + i * 7, .9, 58) for i in range(8))
                + _path("M34 183L104 205M30 210L92 229M174 282L246 310",
                        stroke=c.gold, width=1.3)
                + _spark(220, 159, 7, c))
    if n == 9:
        return (_path("M47 314H230", stroke=c.ink, width=2.5)
                + "".join(w(58 + i*23, 286, .95) for i in range(8))
                + p(144, 360, 1.12) + _path("M132 292L151 296", stroke=c.paper, width=4)
                + w(176, 343, .9, 6)
                + _path("M44 355Q140 324 241 354", stroke=c.gold, width=1.4))
    if n == 10:
        return (_path("M161 296V235L181 221V291M181 295V207L201 190L221 208V293"
                      "M221 291V222L243 207V283", c.warm, c.gold, 1.2)
                + _path("M196 260V227Q202 221 208 227V258M171 264V250M230 257V245",
                        stroke=c.ink, width=1.3)
                + _path("M40 361Q100 307 158 325Q198 304 246 320",
                        stroke=c.gold, width=2)
                + p(108, 358, 1.15, "kneel")
                + "".join(w(104 + i*8, 251 - i*2, .95, -30 + i*6) for i in range(10))
                + _path("M59 354Q102 327 145 332", stroke=c.ink, width=1.1)
                + _spark(203, 183, 6, c))
    if n == 11:
        return (p(132, 355, 1.5) + w(190, 292, 1.45, -6, True)
                + _path("M62 354Q104 327 126 348M174 347Q208 319 236 345",
                        stroke=c.gold, width=1.5)
                + _spark(88, 198, 6, c))
    if n == 12:
        return (_horse(134, 347, 1.55, c, True) + p(136, 292, 1)
                + w(154, 210, 1.4, -12, True)
                + _path("M36 332L79 305M42 348L85 321M181 265L235 236",
                        stroke=c.gold, width=1.4))
    if n == 13:
        return (_path("M60 365V250Q140 202 220 250V365", c.pale, c.gold, 1.5)
                + p(137, 347, 1.33, "sitting", cloak=c.accent)
                + w(205, 284, 1.1) + _tree(81, 346, .85, c, True)
                + _path("M85 311Q75 288 66 312", c.deep, c.ink, 1.1)
                + _spark(143, 195, 10, c))
    return (_path("M60 365V215L82 196H198L220 215V365", c.pale, c.ink, 2)
            + _path("M82 197L140 160L198 197M62 235H218", stroke=c.gold, width=2)
            + p(138, 349, 1.4, "sitting") + w(204, 267, 1.2, 0, True)
            + _path("M91 267Q106 239 119 267M161 266Q177 239 191 267",
                    stroke=c.gold, width=1.6)
            + _spark(140, 183, 10, c))


def _cups(n: int, c: _Colors) -> str:
    cup = lambda x, y, s=1: _cup(x, y, s, c)
    p = lambda x, y, s=1, pose="standing", face=1, cloak=None: _person(x, y, s, c, pose, face, cloak)
    if n == 1:
        return (cup(140, 269, 2.25)
                + _path("M97 211Q77 269 91 310Q117 327 116 346M183 211Q202 263 188 310Q166 326 165 347",
                        stroke=c.accent, width=5)
                + _path("M127 170Q139 153 150 170Q140 172 127 170Z", c.paper, c.gold, 1.2)
                + _path("M139 171V195", stroke=c.gold, width=2)
                + _spark(140, 131, 9, c))
    if n == 2:
        return (_path("M36 339Q140 290 244 339", stroke=c.gold, width=3)
                + p(80, 344, 1.13, face=1) + p(200, 344, 1.13, face=-1)
                + cup(115, 264, .72) + cup(166, 264, .72)
                + _path("M105 262Q140 242 175 262", stroke=c.ink, width=2)
                + _path("M128 204Q140 190 152 204Q154 217 140 228Q126 217 128 204Z",
                        c.warm, c.gold, 1.2))
    if n == 3:
        return (_circle(140, 269, 74, "none", c.gold, 1.5)
                + p(93, 348, .94) + p(140, 323, .94) + p(189, 348, .94)
                + cup(68, 242, .76) + cup(140, 205, .76) + cup(213, 242, .76)
                + "".join(_spark(x, y, 5, c) for x, y in ((76, 302), (119, 183), (200, 304)))
                + _path("M50 353Q140 316 230 353", stroke=c.accent, width=2))
    if n == 4:
        return (_tree(180, 341, 1.6, c) + p(122, 354, 1.15, "sitting")
                + "".join(cup(x, 339, .58) for x in (68, 91, 114))
                + cup(216, 222, .78)
                + _path("M197 238Q216 250 237 236", stroke=c.gold, width=2)
                + _path("M172 340Q188 319 225 328", stroke=c.ink, width=1.2))
    if n == 5:
        return (_path("M54 302Q108 280 142 305Q181 277 239 299", stroke=c.gold, width=2)
                + p(140, 349, 1.25, "kneel")
                + cup(73, 351, .66) + cup(96, 354, .66) + cup(118, 357, .66)
                + cup(195, 330, .72) + cup(221, 332, .72)
                + _path("M47 355Q140 307 244 352", stroke=c.accent, width=1.4)
                + _path("M172 269Q190 251 205 265", stroke=c.gold, width=1.3))
    if n == 6:
        return (_path("M52 344V197Q140 153 228 197V344M67 342V207Q140 177 213 207V342",
                      stroke=c.gold, width=1.8)
                + p(108, 356, .91) + p(179, 356, .8, face=-1)
                + cup(142, 274, .7) + _path("M139 244Q130 235 134 230Q140 235 142 239"
                                       "Q145 227 152 229Q153 236 145 245Z", c.accent, c.gold, 1)
                + _circle(140, 213, 10, c.warm, c.gold, 1.2))
    if n == 7:
        visions = [(64, 204), (117, 181), (172, 186), (218, 212),
                   (76, 276), (141, 269), (204, 278)]
        return (_path("M37 316Q140 267 243 316", stroke=c.gold, width=1.4)
                + "".join(_circle(x, y, 29, c.paper, c.gold, 1.1, .73)
                          + cup(x, y+13, .45) for x, y in visions)
                + _spark(117, 161, 8, c)
                + _path("M168 148L181 160L168 172L155 160Z", c.accent, c.ink, 1)
                + _path("M194 251L205 230L216 251Z", c.deep, c.gold, 1)
                + p(140, 366, .58, "sitting"))
    if n == 8:
        return (_path("M43 363Q114 329 155 337Q195 307 244 316", stroke=c.gold, width=2)
                + "".join(cup(65 + (i%4)*34, 341 - (i//4)*39, .62) for i in range(8))
                + p(208, 307, .89, face=-1)
                + _path("M201 293L244 240", stroke=c.ink, width=1.4)
                + _spark(212, 183, 6, c))
    if n == 9:
        return (_path("M48 281Q140 230 232 281V349H48Z", c.mid, c.ink, 1.8)
                + "".join(cup(68+(i%5)*35, 278+(i//5)*36, .49) for i in range(9))
                + p(140, 351, 1.03, "sitting")
                + _path("M57 349H222", stroke=c.gold, width=2))
    if n == 10:
        return (_path("M48 279Q140 139 232 279", stroke=c.gold, width=7, opacity=.7)
                + "".join(cup(52+i*19.5, 260-((i-4.5)**2*-4+83), .4)
                          for i in range(10))
                + _path("M75 353V282L141 241L208 282V353Z", c.warm, c.ink, 1.5)
                + _path("M110 351V299H171V351", stroke=c.gold, width=1.5)
                + p(106, 358, .73) + p(170, 358, .73, face=-1)
                + _spark(140, 203, 7, c))
    if n == 11:
        return (p(136, 355, 1.42) + cup(186, 270, .91)
                + _path("M174 240Q185 225 194 240Q185 247 174 240Z", c.accent, c.ink, 1.2)
                + _circle(190, 238, 1.5, c.paper)
                + _path("M38 359Q85 337 124 349T242 344", stroke=c.gold, width=1.4)
                + _spark(70, 193, 6, c))
    if n == 12:
        return (_horse(137, 346, 1.4, c) + p(136, 291, .96)
                + cup(171, 234, .9)
                + _path("M38 345Q140 314 242 345", stroke=c.gold, width=1.5)
                + _spark(140, 176, 7, c))
    if n == 13:
        return (_path("M60 364V260Q140 219 220 260V364", c.pale, c.gold, 1.6)
                + p(140, 351, 1.3, "sitting", cloak=c.accent)
                + cup(203, 283, 1)
                + _path("M41 352Q69 338 90 351M190 349Q217 334 241 351",
                        stroke=c.accent, width=1.7)
                + _spark(140, 192, 10, c))
    return (_path("M55 364V218L85 192H195L225 218V364", c.pale, c.ink, 1.8)
            + _path("M83 195Q140 166 197 195", stroke=c.gold, width=2)
            + p(140, 353, 1.38, "sitting") + cup(203, 278, .94)
            + _path("M40 331Q68 315 91 336M188 337Q213 315 242 335",
                    stroke=c.accent, width=2)
            + _spark(140, 177, 8, c))


def _swords(n: int, c: _Colors) -> str:
    sw = lambda x, y, s=1, a=0: _sword(x, y, s, c, a)
    p = lambda x, y, s=1, pose="standing", face=1, cloak=None: _person(x, y, s, c, pose, face, cloak)
    if n == 1:
        return (_rays(140, 207, c, 18, 110) + sw(140, 240, 2.4)
                + _path("M94 201L106 181L121 194L140 177L159 194L174 181L186 201Z",
                        c.gold, c.ink, 1.3)
                + _path("M96 199Q140 211 184 199", stroke=c.ink, width=1.3)
                + _spark(214, 260, 8, c))
    if n == 2:
        return (p(140, 354, 1.33, "sitting")
                + sw(106, 270, 1.1, -63) + sw(174, 270, 1.1, 63)
                + _path("M127 264L154 263", stroke=c.gold, width=4)
                + _path("M47 352Q139 313 233 352", stroke=c.accent, width=1.5)
                + _circle(140, 169, 22, c.paper, c.gold, 1.2))
    if n == 3:
        return (_path("M140 316Q54 261 75 200Q91 165 140 198Q189 165 205 200"
                      "Q225 261 140 316Z", c.mid, c.ink, 2)
                + sw(92, 224, 1.3, -24) + sw(140, 203, 1.5) + sw(188, 224, 1.3, 24)
                + "".join(_path(f"M{x} {y}L{x-11} {y+26}", stroke=c.accent, width=1.7)
                          for x, y in ((52, 152), (79, 140), (201, 142), (229, 156)))
                + _path("M41 346Q140 329 240 347", stroke=c.gold, width=1.3))
    if n == 4:
        return (_path("M51 341V193Q140 130 229 193V341", c.pale, c.gold, 1.7)
                + _path("M95 207L140 162L185 207L140 249Z", c.warm, c.ink, 1.1)
                + _path("M140 167V247M99 208H181M111 191L169 225M169 191L111 225",
                        stroke=c.gold, width=1)
                + _path("M64 299L77 270L89 299M190 298L203 269L216 299",
                        stroke=c.accent, width=1.1)
                + _path("M66 311H216V350H66Z", c.deep, c.ink, 1.6)
                + _path("M74 318H208M74 340H208", stroke=c.gold, width=1.2)
                + _circle(92, 309, 9, c.paper, c.ink, 1.3)
                + _path("M84 307Q85 294 93 294Q102 296 102 306Q93 300 84 307Z", c.ink)
                + _path("M101 306Q119 298 147 303L184 311L205 317V329H99Z",
                        c.mid, c.ink, 1.4)
                + _path("M104 311Q139 315 181 313M118 303L137 319M140 303L160 318",
                        stroke=c.gold, width=1)
                + "".join(sw(x, 276, .68, 90) for x in (89, 142, 195))
                + sw(140, 211, .55))
    if n == 5:
        return (p(140, 348, 1.22)
                + sw(111, 307, .8, -24) + sw(174, 311, .8, 23)
                + "".join(sw(x, y, .65, a) for x, y, a in ((68, 333, 65),
                                                            (208, 339, -75), (176, 355, 85)))
                + p(57, 309, .55, face=-1) + p(226, 316, .5)
                + _path("M36 357Q140 318 244 358", stroke=c.gold, width=1.4))
    if n == 6:
        return (_path("M43 320Q133 342 237 315L211 349Q135 365 63 345Z", c.deep, c.ink, 2)
                + _path("M53 345Q140 371 230 342", stroke=c.gold, width=1.2)
                + p(120, 315, .7, "sitting") + p(159, 314, .55, "sitting")
                + "".join(sw(77+i*26, 280+(i%2)*7, .59) for i in range(6))
                + _path("M227 316L242 252", stroke=c.ink, width=2.4))
    if n == 7:
        return (_path("M50 304V244L73 230L96 244V304M181 300V240L205 223L229 240V300",
                      stroke=c.gold, width=1.6)
                + p(135, 349, 1.08, face=-1)
                + "".join(sw(x, y, .73, 27) for x, y in ((95, 275), (110, 264),
                                                          (127, 255), (145, 267), (159, 278)))
                + sw(58, 342, .72) + sw(223, 342, .72)
                + _path("M42 356Q138 327 241 350", stroke=c.accent, width=1.5))
    if n == 8:
        return (_path("M58 304Q140 260 219 304M59 320Q140 274 220 320", stroke=c.gold, width=1.4)
                + "".join(sw(x, 305+(i%2)*13, .83, (-8 if i%2 else 8))
                          for i, x in enumerate((49, 73, 99, 122, 159, 184, 208, 232)))
                + p(140, 353, 1.08)
                + _path("M128 274L151 274", stroke=c.gold, width=4)
                + _path("M129 329Q141 319 155 330", stroke=c.paper, width=2))
    if n == 9:
        return (_path("M39 345V241L114 221L207 242V345Z", c.pale, c.ink, 1.5)
                + _path("M158 220V267M180 233V267M202 241V267", stroke=c.gold, width=1.2)
                + _path("M54 320H222V348H54Z", c.deep, c.ink, 2)
                + _path("M61 328H216M61 342H216", stroke=c.gold, width=1)
                + p(124, 319, .9, "sitting")
                + _path("M107 260Q122 248 139 263", stroke=c.ink, width=1.2)
                + "".join(_path(f"M{56+i*20} {229-(i%3)*9}L{62+i*20} {211-(i%3)*9}",
                                 stroke=c.gold, width=2.4) for i in range(9))
                + _circle(202, 169, 23, c.paper, c.gold, 1.2)
                + _path("M77 299L89 287M202 298L214 284", stroke=c.accent, width=1.3))
    if n == 10:
        return (_path("M24 290Q140 269 256 293", stroke=c.gold, width=3)
                + _path("M24 305Q140 286 256 308", stroke=c.accent, width=1.8)
                + p(145, 345, 1.2, "fallen")
                + "".join(sw(62+i*18, 290+(i%3)*8, .67, (-7 if i%2 else 7))
                          for i in range(10))
                + _rays(141, 173, c, 12, 85))
    if n == 11:
        return (p(139, 358, 1.35) + sw(186, 257, 1.35, 13)
                + _path("M36 305L99 276M43 330L108 299M171 194L240 174",
                        stroke=c.accent, width=2)
                + _spark(72, 173, 6, c))
    if n == 12:
        return (_horse(136, 346, 1.52, c, True) + p(133, 292, .95)
                + sw(171, 207, 1.18, 38)
                + _path("M32 296L83 264M36 321L86 292M186 161L242 133",
                        stroke=c.accent, width=1.8))
    if n == 13:
        return (_path("M60 364V244L87 225H193L220 244V364", c.pale, c.gold, 1.5)
                + p(141, 348, 1.38, "sitting") + sw(201, 253, 1.2)
                + _path("M67 251Q140 223 213 251", stroke=c.ink, width=1.1)
                + _spark(139, 191, 9, c))
    return (_path("M57 364V218L85 194H195L223 218V364", c.pale, c.ink, 1.7)
            + p(140, 349, 1.42, "sitting") + sw(202, 260, 1.22)
            + _path("M82 195L140 163L198 195M80 245H201", stroke=c.gold, width=1.5)
            + _path("M88 221Q96 210 104 221Q97 232 88 221ZM174 221Q182 210 190 221"
                    "Q182 232 174 221Z", c.accent, c.gold, 1)
            + _spark(141, 181, 8, c))


def _pentacles(n: int, c: _Colors) -> str:
    coin = lambda x, y, r=15, detail=True: _coin(x, y, r, c, detail)
    p = lambda x, y, s=1, pose="standing", face=1, cloak=None: _person(x, y, s, c, pose, face, cloak)
    if n == 1:
        return (_path("M57 355V232Q140 177 224 232V355M72 354V242Q140 200 209 242V354",
                      stroke=c.gold, width=2)
                + _path("M42 305Q83 278 109 292L129 278L143 289L116 306L70 328Z",
                        c.paper, c.ink, 1.8)
                + coin(152, 230, 37)
                + _path("M42 353Q141 316 239 353", stroke=c.accent, width=2))
    if n == 2:
        return (p(140, 349, 1.1) + coin(89, 255, 22) + coin(191, 269, 22)
                + _path("M96 255Q129 206 167 257Q196 300 159 320Q116 331 89 281",
                        stroke=c.gold, width=4)
                + _path("M42 353Q91 333 141 353T242 353", stroke=c.accent, width=2)
                + _path("M62 305H94L84 313H71Z", c.deep, c.ink, 1))
    if n == 3:
        return (_path("M43 358V197Q140 135 237 197V358M53 358V203Q140 153 227 203V358",
                      stroke=c.ink, width=2)
                + "".join(coin(x, 208, 16) for x in (91, 140, 189))
                + p(96, 347, .88) + p(140, 336, .94) + p(186, 347, .86)
                + _path("M64 351H220M77 302H202", stroke=c.gold, width=1.8)
                + _path("M162 298L182 281L203 301", stroke=c.accent, width=1.1))
    if n == 4:
        return (_path("M51 356V255L82 231H198L229 255V356", c.mid, c.ink, 1.5)
                + p(140, 348, 1.32, "sitting")
                + coin(140, 290, 20) + coin(139, 203, 17)
                + coin(84, 352, 14) + coin(196, 352, 14)
                + _path("M62 357H218", stroke=c.gold, width=2))
    if n == 5:
        return (_path("M49 288V197Q140 140 231 197V288", c.deep, c.gold, 2)
                + _path("M60 281V205Q140 157 220 205V281", c.warm, c.ink, 1)
                + "".join(coin(x, y, 14, False) for x, y in ((103, 217), (140, 201),
                                                               (178, 218), (120, 254), (160, 254)))
                + p(100, 355, .96, face=-1) + p(183, 353, .86)
                + "".join(_spark(x, y, 3, c) for x, y in ((52, 317), (217, 326), (85, 296)))
                + _path("M35 359Q139 330 245 359", stroke=c.paper, width=2))
    if n == 6:
        return (p(140, 333, 1.18)
                + _path("M103 231L140 241L177 231M140 241V262M111 272H169",
                        stroke=c.gold, width=2.5)
                + coin(107, 273, 10) + coin(174, 273, 10)
                + "".join(coin(x, y, 9, False) for x, y in ((62, 209), (218, 209),
                                                              (83, 184), (197, 184)))
                + _path("M46 353Q77 326 104 343M177 343Q209 326 237 353",
                        stroke=c.ink, width=3.2))
    if n == 7:
        return (_tree(167, 347, 1.45, c, True)
                + "".join(coin(x, y, 10, False) for x, y in ((133, 226), (174, 210),
                            (202, 227), (128, 253), (170, 249), (206, 260), (154, 281)))
                + p(72, 356, 1.13) + _path("M98 340L126 291", stroke=c.ink, width=2.5)
                + _path("M45 359Q140 330 239 359", stroke=c.gold, width=1.5))
    if n == 8:
        return (_path("M47 338H230V359H47Z", c.deep, c.ink, 1.6)
                + p(94, 335, 1.02, "sitting")
                + "".join(coin(170 + (i%2)*29, 212 + (i//2)*34, 11, False)
                          for i in range(8))
                + _path("M96 284L154 263", stroke=c.gold, width=2.4)
                + _spark(211, 188, 6, c))
    if n == 9:
        return (_path("M46 359Q140 286 236 359", stroke=c.gold, width=2)
                + "".join(_path(f"M{x} 359V{270+(i%2)*20}", stroke=c.accent, width=3)
                          + _circle(x, 272+(i%2)*20, 6, c.accent)
                          for i, x in enumerate((61, 82, 104, 126, 158, 180, 202, 224)))
                + p(141, 349, 1.12) + coin(139, 205, 18)
                + _path("M103 214Q118 201 127 214", stroke=c.ink, width=1.2))
    if n == 10:
        return (_path("M45 359V192Q140 135 235 192V359M61 359V200Q140 160 219 200V359",
                      stroke=c.gold, width=2)
                + "".join(coin(x, y, 10, False) for x, y in ((79, 209), (109, 184),
                           (140, 176), (171, 184), (201, 209), (71, 271), (209, 271),
                           (93, 319), (140, 303), (187, 319)))
                + p(103, 355, .72) + p(172, 355, .72, face=-1)
                + _path("M124 356Q140 342 156 356", stroke=c.ink, width=3))
    if n == 11:
        return (p(140, 354, 1.45) + coin(193, 250, 23)
                + _path("M42 355Q90 326 126 347M169 344Q212 317 240 344",
                        stroke=c.accent, width=2)
                + _spark(75, 203, 5, c))
    if n == 12:
        return (_horse(137, 349, 1.43, c) + p(137, 291, .92)
                + coin(187, 256, 17)
                + "".join(_path(f"M37 {y}Q139 {y-17} 243 {y}", stroke=c.gold,
                                 width=1.2) for y in (332, 350, 368)))
    if n == 13:
        return (_path("M57 365V243Q140 198 223 243V365", c.pale, c.gold, 1.5)
                + p(139, 348, 1.33, "sitting", cloak=c.accent)
                + coin(201, 267, 19) + _tree(72, 345, .58, c, True)
                + _path("M204 344Q224 328 231 350Q213 356 204 344Z", c.paper, c.ink, 1)
                + _spark(140, 191, 8, c))
    return (_path("M55 365V217L85 190H195L225 217V365", c.pale, c.ink, 1.7)
            + _path("M85 191L140 158L195 191M55 236H225", stroke=c.gold, width=1.8)
            + p(140, 350, 1.38, "sitting") + coin(202, 271, 20)
            + _path("M71 352Q91 325 110 352M173 351Q193 321 214 351",
                    stroke=c.accent, width=2.3)
            + _spark(140, 177, 8, c))


ART_NOTES = {
    ("Wands", 1): "A single sprouting staff catches fire while an open hand offers it to the world.",
    ("Wands", 2): "Two staffs frame a traveler above the parapet, with an entire horizon still to choose.",
    ("Wands", 3): "Ships have already left the shore; the three staffs keep watch for what returns.",
    ("Wands", 4): "Four living posts hold a garland over the small figures gathered below it.",
    ("Wands", 5): "Five staffs cross at different angles, turning shared fire into useful friction.",
    ("Wands", 6): "A rider carries the laurel through a street full of little answering lights.",
    ("Wands", 7): "One figure stands on the dark ridge while six staffs rise from below.",
    ("Wands", 8): "Eight staffs streak across open air toward a landing place still out of view.",
    ("Wands", 9): "The watchful figure stands before a fence of eight staffs, one more at hand.",
    ("Wands", 10): "A heavy bundle leans over a kneeling traveler while the town is already near.",
    ("Wands", 11): "The Page studies a living flame at the tip of a staff rather than a finished map.",
    ("Wands", 12): "Horse and rider cut through the hot landscape with the wand held forward.",
    ("Wands", 13): "The Queen keeps a sunflower-like light above her garden and its watchful cat.",
    ("Wands", 14): "The King's angular seat and lit staff turn raw fire into a place to build.",
    ("Cups", 1): "Water pours from the great chalice on both sides, making room beyond its rim.",
    ("Cups", 2): "Two figures meet across the bridge and raise their cups into the same space.",
    ("Cups", 3): "Three friends and three cups complete a circle that leaves room to enter.",
    ("Cups", 4): "The offered cup floats beside the tree while the seated figure looks inward.",
    ("Cups", 5): "Spilled vessels lie near the grieving figure; two full cups remain beyond.",
    ("Cups", 6): "Two small figures share a flower cup in an old courtyard under a round window.",
    ("Cups", 7): "Seven translucent vessels present dreams, but only one path begins at the bottom.",
    ("Cups", 8): "Eight cups remain at the shore as the traveler walks toward the moonlit rise.",
    ("Cups", 9): "The seated figure rests before a shelf of cups, allowing enoughness to be seen.",
    ("Cups", 10): "A bright arch of cups rises over a home and the people who tend it.",
    ("Cups", 11): "A small fish surfaces from the Page's cup like a message from another world.",
    ("Cups", 12): "The Knight offers a cup while the horse pauses before the crossing.",
    ("Cups", 13): "The Queen sits by moving water with an ornate vessel held within reach.",
    ("Cups", 14): "The King's throne stays centered while water moves on either side.",
    ("Swords", 1): "A single blade passes through a crown and opens a field of clear light.",
    ("Swords", 2): "Crossed swords guard a seated figure whose covered eyes face the sea.",
    ("Swords", 3): "Three blades pierce one heart while rain marks the space around it.",
    ("Swords", 4): "A resting figure lies below the bright window with three blades laid aside.",
    ("Swords", 5): "Scattered swords surround the central figure as others leave the field.",
    ("Swords", 6): "Six swords travel upright in the boat, carried rather than denied.",
    ("Swords", 7): "Five blades travel with a quiet figure while two remain by the tents.",
    ("Swords", 8): "The sword ring has a visible opening even as the figure stands inside it.",
    ("Swords", 9): "Nine cuts of light hover above the bed in the room of sleepless thought.",
    ("Swords", 10): "Ten blades stand at a hard horizon while dawn begins behind them.",
    ("Swords", 11): "The Page lifts one precise blade into wind that has no fixed direction.",
    ("Swords", 12): "The Knight's horse breaks forward under a blade angled into the storm.",
    ("Swords", 13): "The Queen's upright sword rises beside an open seat and a clearing sky.",
    ("Swords", 14): "The King's blade and paired wing marks place judgment inside a wider view.",
    ("Pentacles", 1): "A hand brings a marked coin through the garden gate toward workable ground.",
    ("Pentacles", 2): "Two coins move inside a looping ribbon while a small ship rides the waves.",
    ("Pentacles", 3): "Three makers meet beneath the workshop's three round emblems.",
    ("Pentacles", 4): "One coin is held, one crowns the figure, and two pin the feet to the city.",
    ("Pentacles", 5): "Two travelers pass a lit five-part window on a road of snow.",
    ("Pentacles", 6): "Balanced scales hover above small coins and the hands reaching toward them.",
    ("Pentacles", 7): "Seven coins grow in the tree while the cultivator pauses to look closely.",
    ("Pentacles", 8): "A maker studies the workbench while eight finished pieces line the wall.",
    ("Pentacles", 9): "The vineyard's ordered growth surrounds a solitary figure with a bright coin.",
    ("Pentacles", 10): "Ten emblems make an arch wide enough to shelter more than one life.",
    ("Pentacles", 11): "The Page holds a material possibility beside a field ready to be worked.",
    ("Pentacles", 12): "The Knight carries one coin at a deliberate pace across plowed ground.",
    ("Pentacles", 13): "The Queen's garden seat includes the coin, flowering tree, and small animal.",
    ("Pentacles", 14): "Vines climb the King's stone seat while the coin rests at hand.",
}


def render_minor(card: dict, palette) -> str:
    """Return the clipped illustration for one Minor Arcana card."""
    suit, number = card["suit"], card["number"]
    if suit not in ("Wands", "Cups", "Swords", "Pentacles") or number not in range(1, 15):
        raise ValueError(f"Unsupported minor card: {suit} {number}")
    colors = _Colors(palette, suit)
    scene = {"Wands": _wands, "Cups": _cups,
             "Swords": _swords, "Pentacles": _pentacles}[suit](number, colors)
    # The plate expands into Ominity's 346px art window without stretching the
    # linework horizontally; keeping the transformation vector-side preserves
    # crispness on both high-DPI and theme-switched displays.
    return ('<g transform="translate(0 -20.48) scale(1 1.12)">'
            + _world(colors, suit, number) + _architecture(colors, suit, number) + scene + '</g>')
