"""Original, theme-drawn tableaux for Ominity's Major Arcana.

These plates use traditional tarot *symbols*, not another deck's compositions.
Every shape stays vector sharp at display scale.  The shell supplies a clip at
x=24..256, y=68..414; this module deliberately draws beyond it for full bleed.
"""

from __future__ import annotations

import math


ART_NOTES = {
    0: "A traveler pauses at a cut in the stone while the little dog faces the open sky.",
    1: "One hand reaches into the halo; the other points to four tools on the worktable.",
    2: "The moon hangs in the narrow space between two pillars, with water visible beyond the veil.",
    3: "Grain rises around the seated figure, while a river threads through the garden behind her.",
    4: "The mountain and the throne echo each other's hard geometry, but a small flame remains free.",
    5: "Two small listeners stand beneath an arch as the teacher opens a book above crossed keys.",
    6: "Two figures face one another across a narrow path, with trees framing the same sun.",
    7: "A still driver holds a line between a pale horse and a dark horse beneath a canopy of stars.",
    8: "A human hand rests on the lion's mane; the infinity loop floats above their shared calm.",
    9: "The lantern lights only the next turn of a steep path, leaving the farther mountain unresolved.",
    10: "Four tiny stars keep their corners while the eight-spoked wheel turns in the center.",
    11: "A sword divides the space vertically; the two pans hang level in front of a seated witness.",
    12: "The suspended figure's face sits inside a bright halo as the entire landscape turns around them.",
    13: "A dark gate frames a setting sun, and one new shoot crosses the threshold.",
    14: "A stream travels between two vessels in the hands of a figure standing in two waters.",
    15: "The chains look heavy, yet each can be opened by a figure beneath the shadow.",
    16: "The lightning strikes the crown of the tower; falling stones expose a clear patch of ground.",
    17: "The largest star shines over a figure who pours water both into the pool and onto the earth.",
    18: "Two watchful animals flank a wavering path that disappears between distant towers.",
    19: "A rider and horse move through sunflowers beneath a sun that takes up nearly the whole sky.",
    20: "A call passes across the horizon as three figures rise from separate stone frames.",
    21: "A dancer steps inside an unclosed wreath, with four witnesses at the edges of the world.",
}


def _mix(a: str, b: str, t: float) -> str:
    ca = tuple(int(a[i:i + 2], 16) for i in (1, 3, 5))
    cb = tuple(int(b[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x * (1 - t) + y * t):02x}" for x, y in zip(ca, cb))


def _p(d: str, fill: str = "none", stroke: str = "none", width: float = 1.5,
       extra: str = "") -> str:
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round" {extra}/>' )


def _c(x: float, y: float, r: float, fill: str = "none", stroke: str = "none",
       width: float = 1.5, extra: str = "") -> str:
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}" {extra}/>' )


def _r(x: float, y: float, w: float, h: float, fill: str = "none",
       stroke: str = "none", width: float = 1.5, extra: str = "") -> str:
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}" {extra}/>' )


def _g(markup: str, transform: str) -> str:
    return f'<g transform="{transform}">{markup}</g>'


_ELEMENT_SUIT = (
    "Swords", "Wands", "Cups", "Pentacles", "Wands", "Pentacles",
    "Cups", "Wands", "Wands", "Pentacles", "Swords", "Swords",
    "Cups", "Pentacles", "Cups", "Pentacles", "Wands", "Cups",
    "Cups", "Wands", "Swords", "Pentacles",
)


class _Colors:
    def __init__(self, palette, number: int):
        self.paper = palette.paper
        self.ink = palette.ink
        self.gold = palette.gold
        self.accent = palette.accents.get(_ELEMENT_SUIT[number], palette.gold)
        self.pale = _mix(palette.paper, palette.ink, .10)
        self.haze = _mix(palette.paper, palette.gold, .20)
        self.distant = _mix(_mix(palette.paper, palette.ink, .23), self.accent, .20)
        self.mid = _mix(_mix(palette.paper, palette.ink, .46), self.accent, .13)
        self.deep = _mix(palette.paper, palette.ink, .84)
        self.light = _mix(palette.paper, palette.gold, .40)
        self.edge = _mix(palette.ink, palette.paper, .20)


def _sky(n: int, c: _Colors, *, night: bool = False) -> str:
    upper = _mix(_mix(c.paper, c.ink if night else c.gold,
                      .27 if night else .16), c.accent, .12)
    lower = _mix(c.paper, c.accent, .10 if night else .05)
    return (f'<defs><linearGradient id="maj-sky-{n}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{upper}"/>'
            f'<stop offset="1" stop-color="{lower}"/></linearGradient></defs>'
            + _r(24, 68, 232, 346, f'url(#maj-sky-{n})'))


def _orb(x: float, y: float, radius: float, c: _Colors, *, moon: bool = False) -> str:
    rings = "".join(_c(x, y, radius + k, "none", c.gold, .6, 'opacity=".55"')
                    for k in (9, 17))
    rays = "".join(_p(f"M{x + math.cos(math.radians(a)) * (radius + 24):.1f} "
                      f"{y + math.sin(math.radians(a)) * (radius + 24):.1f}L"
                      f"{x + math.cos(math.radians(a)) * (radius + 34):.1f} "
                      f"{y + math.sin(math.radians(a)) * (radius + 34):.1f}",
                      stroke=c.gold, width=.9)
                   for a in range(0, 360, 30))
    disc = _c(x, y, radius, c.light, c.gold, 1.8)
    if moon:
        disc += _c(x + radius * .32, y - radius * .13, radius * .87, c.pale)
    return rings + rays + disc


def _star(x: float, y: float, r: float, c: _Colors, filled: bool = True) -> str:
    points = []
    for i in range(8):
        angle = math.pi * i / 4 - math.pi / 2
        rr = r if i % 2 == 0 else r * .22
        points.append((x + math.cos(angle) * rr, y + math.sin(angle) * rr))
    d = "M" + "L".join(f"{px:.1f} {py:.1f}" for px, py in points) + "Z"
    return _p(d, c.gold if filled else "none", c.gold, .85)


def _constellation(c: _Colors, points: tuple[tuple[int, int, float], ...]) -> str:
    return "".join(_star(x, y, r, c) for x, y, r in points)


def _mountains(c: _Colors, horizon: int = 300, *, near: bool = True) -> str:
    far = _p(f"M24 {horizon}L69 {horizon-81}L95 {horizon-48}L135 {horizon-116}"
             f"L166 {horizon-56}L206 {horizon-96}L256 {horizon-25}V414H24Z",
             c.distant, c.mid, 1.1)
    far += _p(f"M65 {horizon-75}L69 {horizon-81}L76 {horizon-73}"
              f"M130 {horizon-109}L135 {horizon-116}L141 {horizon-105}"
              f"M201 {horizon-91}L206 {horizon-96}L211 {horizon-86}",
              stroke=c.paper, width=1.2)
    if not near:
        return far
    return far + _p(f"M24 {horizon+24}Q75 {horizon-14} 116 {horizon+15}"
                    f"Q167 {horizon-11} 256 {horizon+26}V414H24Z", c.mid)


def _horizon(c: _Colors, y: int = 316) -> str:
    return (_p(f"M24 {y}Q80 {y-17} 140 {y}T256 {y}V414H24Z", c.distant)
            + _p(f"M24 {y+27}Q91 {y-5} 140 {y+23}T256 {y+20}V414H24Z", c.mid)
            + _p(f"M24 {y+49}Q98 {y+14} 145 {y+47}T256 {y+42}",
                 stroke=c.edge, width=1.2))


def _water(c: _Colors, y: int = 318, rows: int = 6) -> str:
    return (_p(f"M24 {y}Q116 {y-11} 256 {y+4}V414H24Z", c.distant)
            + "".join(_p(f"M{34 + (i % 2)*13} {y+9+i*12}"
                          f"Q88 {y+4+i*12} 129 {y+9+i*12}"
                          f"T245 {y+9+i*12}", stroke=c.mid, width=.8,
                          extra='opacity=".72"') for i in range(rows)))


def _ground(c: _Colors, y: int = 345) -> str:
    return (_p(f"M24 {y}Q73 {y-13} 139 {y+1}Q207 {y-12} 256 {y}V414H24Z",
               c.deep)
            + _p(f"M24 {y}Q73 {y-13} 139 {y+1}Q207 {y-12} 256 {y}",
                 stroke=c.gold, width=1.1))


def _grass(x: float, y: float, c: _Colors, s: float = 1) -> str:
    return _g(_p("M0 0Q-7 -17 -5 -27M0 0Q1 -17 8 -32M0 0Q8 -12 15 -16",
                 stroke=c.gold, width=1.1), f"translate({x} {y}) scale({s})")


def _flower(x: float, y: float, c: _Colors, s: float = 1) -> str:
    petals = "".join(_p(f"M0 0Q{dx*8-dy*4} {dy*8+dx*4} {dx*11} {dy*11}"
                         f"Q{dx*8+dy*4} {dy*8-dx*4} 0 0Z", c.light, c.gold, .8)
                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    return _g(petals + _c(0, 0, 2, c.gold), f"translate({x} {y}) scale({s})")


def _tree(x: int, y: int, c: _Colors, scale: float = 1, *, bare: bool = False) -> str:
    trunk = _p("M0 0Q-5 -47 -1 -104M-1 -76Q-21 -105 -32 -119"
               "M-1 -90Q14 -123 29 -137M-4 -50Q-22 -65 -43 -65",
               stroke=c.deep, width=4.2)
    twig = _p("M-29 -116L-42 -128M23 -132L34 -147M-31 -66L-44 -78",
              stroke=c.mid, width=1.4)
    leaves = "" if bare else "".join(
        _p(f"M{xx} {yy}q-13 -8 -11 -19q13 0 17 13Z", c.mid, c.gold, .6)
        for xx, yy in ((-32, -120), (-15, -107), (22, -135), (33, -143), (-42, -70)))
    return _g(trunk + twig + leaves, f"translate({x} {y}) scale({scale})")


def _figure(x: int, y: int, c: _Colors, scale: float = 1, *, robe: str | None = None,
            facing: int = 1, arms: str = "down", head: str | None = None) -> str:
    """Faceted human icon; y is ground plane, design height approximately 102."""
    garment = robe or c.deep
    face = head or c.pale
    arm_path = {
        "down": "M-10 -66Q-22 -44 -20 -25L-16 -23L-5 -55M10 -66Q22 -44 20 -25L16 -23L5 -55",
        "open": "M-11 -65Q-25 -57 -33 -45L-30 -40L-6 -52M10 -65Q25 -57 33 -45L30 -40L6 -52",
        "up": "M-10 -65Q-25 -81 -28 -95L-24 -99L-4 -58M10 -65Q25 -80 27 -95L23 -99L4 -58",
        "oneup": "M-10 -65Q-25 -83 -28 -99L-24 -101L-3 -57M10 -65Q22 -45 20 -24L16 -22L5 -55",
        "point": "M-10 -65Q-25 -50 -34 -43L-33 -38L-4 -54M10 -65Q24 -68 39 -81L40 -87L4 -56",
    }[arms]
    body = (_p("M-8 -66Q0 -72 8 -66L16 -39L20 -5Q0 5 -20 -5L-16 -39Z",
               garment, c.edge, 1.2)
            + _p("M-8 -62Q-4 -37 -13 -13M7 -61Q6 -33 13 -11M-1 -66Q2 -40 0 -2",
                 stroke=c.paper, width=.85, extra='opacity=".72"')
            + _p(arm_path, "none", c.edge, 5.5)
            + _p(arm_path, "none", c.light, 2.7)
            + _c(0, -82, 11, face, c.edge, 1.2)
            + _p("M-11 -84Q-12 -103 2 -103Q15 -99 10 -83Q4 -91 -2 -89Q-7 -84 -11 -84Z",
                 c.deep)
            + _p("M-3 -77Q1 -75 5 -78", stroke=c.edge, width=.8)
            + _p("M-19 -4L-22 1M18 -4L22 1", stroke=c.edge, width=1.3))
    return _g(body, f"translate({x} {y}) scale({facing * scale} {scale})")


def _cup(x: int, y: int, c: _Colors, s: float = 1) -> str:
    thing = (_p("M-12 -14Q-12 3 0 7Q12 3 12 -14Z", c.light, c.gold, 1.2)
             + _p("M-11 -11Q0 -14 11 -11M0 7V19M-9 20H9", stroke=c.gold, width=1.8))
    return _g(thing, f"translate({x} {y}) scale({s})")


def _sword(x: int, y: int, c: _Colors, s: float = 1, rotate: int = 0) -> str:
    thing = (_p("M0 -39L5 10L0 14L-5 10Z", c.pale, c.deep, 1.2)
             + _p("M-13 14H13M0 14V28", stroke=c.gold, width=2)
             + _c(0, 30, 2.5, c.gold))
    return _g(thing, f"translate({x} {y}) rotate({rotate}) scale({s})")


def _staff(x: int, y: int, c: _Colors, s: float = 1, rotate: int = 0) -> str:
    thing = (_p("M-2 34Q-4 -8 0 -38Q4 -8 2 34Z", c.deep, c.gold, 1.2)
             + _p("M1 -21Q16 -27 15 -42M-1 -4Q-15 -12 -14 -23",
                  stroke=c.gold, width=1.4))
    return _g(thing, f"translate({x} {y}) rotate({rotate}) scale({s})")


def _coin(x: int, y: int, c: _Colors, s: float = 1) -> str:
    return _g(_c(0, 0, 15, c.light, c.gold, 1.7) + _star(0, 0, 11, c, False),
              f"translate({x} {y}) scale({s})")


def _arch(x: int, y: int, w: int, h: int, c: _Colors, *, filled: bool = False) -> str:
    return (_p(f"M{x-w/2} {y+h}V{y+w/2}Q{x} {y-w/2} {x+w/2} {y+w/2}V{y+h}",
               c.pale if filled else "none", c.deep, 3)
            + _p(f"M{x-w/2+9} {y+h}V{y+w/2+2}Q{x} {y-w/2+17} "
                 f"{x+w/2-9} {y+w/2+2}V{y+h}", stroke=c.gold, width=1))


def _platform(c: _Colors, y: int = 346) -> str:
    return (_r(24, y, 232, 7, c.deep)
            + _r(24, y + 7, 232, 35, c.mid)
            + "".join(_p(f"M{x} {y+8}v32", stroke=c.edge, width=.7)
                      for x in range(38, 260, 28)))


def _wheel(x: int, y: int, radius: int, c: _Colors) -> str:
    rings = (_c(x, y, radius, c.pale, c.gold, 4)
             + _c(x, y, radius - 11, "none", c.deep, 1.7)
             + _c(x, y, radius - 22, "none", c.gold, 1.3)
             + _c(x, y, 12, c.light, c.deep, 1.5))
    spokes = "".join(_p(f"M{x} {y-radius+22}V{y-12}", stroke=c.deep, width=1.8,
                        extra=f'transform="rotate({a} {x} {y})"') for a in range(0, 360, 45))
    return rings + spokes


def _lion(x: int, y: int, c: _Colors, s: float = 1) -> str:
    mane = (_p("M-26 -31Q-30 -63 -11 -69Q7 -85 25 -61Q45 -47 30 -28"
               "Q31 -7 6 -3Q-22 -1 -26 -31Z", c.gold, c.deep, 2)
            + _p("M-13 -34Q-26 -20 -34 -4L-17 0Q-2 -17 7 -16M11 -17Q23 -9 30 1",
                 c.mid, c.deep, 1.5)
            + _p("M-15 -48Q-7 -64 10 -58Q25 -51 20 -35L14 -27L-1 -27Z",
                 c.light, c.deep, 1.6)
            + _c(10, -45, 2.2, c.deep)
            + _p("M17 -34Q28 -29 19 -23Q8 -22 2 -28", stroke=c.deep, width=1.3)
            + _p("M-30 -10Q-46 -38 -32 -46", stroke=c.gold, width=2))
    return _g(mane, f"translate({x} {y}) scale({s})")


def _horse(x: int, y: int, c: _Colors, s: float = 1, facing: int = 1,
           color: str | None = None) -> str:
    coat = color or c.mid
    beast = (_p("M-26 -39Q-12 -55 9 -50L25 -66L34 -58L26 -38"
                "Q38 -18 25 -3L5 -8L-13 -2L-26 -4Z", coat, c.deep, 1.5)
             + _p("M22 -60Q7 -77 5 -57M-15 -1L-19 15M9 -4L6 15M27 -3L31 15",
                  stroke=c.deep, width=3)
             + _c(25, -47, 1.8, c.gold)
             + _p("M-24 -37Q-38 -45 -42 -29", stroke=c.gold, width=2))
    return _g(beast, f"translate({x} {y}) scale({facing*s} {s})")


def _major_0(c):
    return (_orb(206, 151, 29, c) + _mountains(c, 311, near=False)
            + _p("M24 251L105 265L127 323L115 348L24 348Z", c.mid, c.deep, 1.7)
            + _p("M24 271L101 282L115 322M24 302L77 308L89 336", stroke=c.paper, width=1)
            + _p("M128 326Q175 351 256 319V414H24V350H112Z", c.distant)
            + _figure(99, 257, c, 1.15, arms="open", robe=c.deep)
            + _staff(58, 190, c, .65, -28)
            + _p("M64 185Q46 177 43 199L70 203Z", c.light, c.gold, 1)
            + _p("M84 263Q64 249 59 269Q65 282 82 278Z", c.pale, c.deep, 1.4)
            + _c(76, 261, 2, c.deep) + _flower(64, 247, c, .6)
            + _grass(36, 348, c, .8) + _star(155, 179, 5, c))


def _major_1(c):
    infinity = _p("M104 134C83 111 78 164 109 146C137 128 143 125 171 146"
                  "C202 164 197 111 176 134C153 158 126 158 104 134Z",
                  stroke=c.gold, width=2.6)
    return (_orb(140, 169, 18, c) + _arch(140, 186, 178, 150, c)
            + _p("M48 349Q88 323 110 338M170 338Q202 322 232 350", stroke=c.mid)
            + _figure(140, 294, c, 1.31, arms="oneup") + infinity
            + _r(47, 308, 186, 9, c.deep, c.gold, 1)
            + _r(55, 317, 5, 48, c.deep) + _r(219, 317, 5, 48, c.deep)
            + _cup(76, 297, c, .7) + _sword(116, 291, c, .55)
            + _staff(171, 288, c, .55, 24) + _coin(206, 292, c, .7)
            + _tree(54, 335, c, .40) + _tree(231, 335, c, .40))


def _major_2(c):
    veil = _p("M70 175Q140 125 210 175V351H70Z", c.haze, c.gold, 1.5,
              extra='opacity=".72"')
    stripes = "".join(_p(f"M{x} 174V345", stroke=c.gold, width=.7,
                         extra='opacity=".52"') for x in range(82, 210, 16))
    return (_orb(140, 166, 25, c, moon=True) + _water(c, 298)
            + veil + stripes + _r(48, 171, 27, 185, c.deep, c.gold, 1.2)
            + _r(205, 171, 27, 185, c.deep, c.gold, 1.2)
            + _p("M47 171Q140 87 233 171", stroke=c.deep, width=5)
            + _p("M58 171Q140 108 222 171", stroke=c.gold, width=1.2)
            + _figure(140, 337, c, 1.12, robe=c.pale)
            + _p("M106 297Q140 287 174 297V322Q140 315 106 322Z", c.paper, c.deep, 1.1)
            + _p("M140 293V319", stroke=c.gold, width=1.3)
            + _c(140, 254, 34, "none", c.gold, 1))


def _major_3(c):
    grain = "".join(_g(_p("M0 0V-64M0 -52Q-9 -62 -7 -70M0 -45Q9 -56 7 -65",
                            stroke=c.gold, width=1.5)
                       + _p("M-7 -70l5 -1M7 -65l5 -3", stroke=c.gold),
                       f"translate({x} 383) scale({s})")
                    for x, s in ((39, .7), (52, 1), (68, .75), (211, .9), (231, .68), (248, 1.1)))
    return (_orb(177, 164, 36, c) + _horizon(c, 305)
            + _p("M256 277Q192 293 165 317Q138 339 45 371", stroke=c.gold, width=4)
            + _tree(58, 346, c, .7) + _tree(237, 347, c, .6)
            + _r(92, 259, 96, 75, c.mid, c.deep, 1.5)
            + _p("M85 270Q140 230 195 270L185 336H95Z", c.light, c.deep, 1.7)
            + _figure(141, 330, c, 1.3, robe=c.light, arms="open")
            + grain + _flower(45, 315, c, .7) + _flower(218, 302, c, .8))


def _major_4(c):
    masonry = "".join(_p(f"M{58+i*24} 216V299M52 237H229M52 260H229",
                        stroke=c.paper, width=.9, extra='opacity=".5"') for i in (0, 2, 4, 6))
    return (_mountains(c, 330, near=False)
            + _p("M24 337L65 292L91 309L135 262L165 290L223 246L256 274V414H24Z", c.mid)
            + _r(51, 214, 178, 126, c.deep, c.gold, 2) + masonry
            + _p("M84 255L84 196L140 155L196 196V255", c.deep, c.gold, 2)
            + _p("M98 210L140 181L182 210", stroke=c.paper, width=1)
            + _figure(140, 342, c, 1.42, robe=c.mid)
            + _staff(204, 283, c, 1.2)
            + _p("M94 337H186", stroke=c.gold, width=2)
            + _p("M38 351Q55 333 71 351M211 351Q229 333 246 351", stroke=c.gold, width=1.5)
            + _p("M44 318q-7 -15 0 -23q10 10 0 23Z", c.gold))


def _major_5(c):
    roof = (_arch(140, 120, 198, 246, c, filled=True)
            + _arch(140, 147, 152, 214, c))
    keys = (_g(_c(0, -11, 8, "none", c.gold, 2) + _p("M0 -3V23M-3 14H4M-3 20H4",
                                             stroke=c.gold, width=2),
               "translate(133 327) rotate(35)")
            + _g(_c(0, -11, 8, "none", c.gold, 2) + _p("M0 -3V23M-3 14H4M-3 20H4",
                                              stroke=c.gold, width=2),
                 "translate(149 327) rotate(-35)"))
    return (roof + _star(140, 152, 10, c) + _platform(c, 350)
            + _figure(140, 311, c, 1.2, robe=c.deep, arms="open")
            + _p("M100 289Q140 273 180 289L180 312Q140 299 100 312Z", c.paper, c.gold, 1.3)
            + _p("M140 282V309", stroke=c.gold, width=1)
            + _figure(74, 359, c, .53, robe=c.mid) + _figure(207, 359, c, .53, robe=c.mid)
            + keys + _p("M49 352H231", stroke=c.gold, width=1))


def _major_6(c):
    bridge = _p("M24 337Q140 287 256 337V414H24Z", c.pale, c.deep, 1)
    return (_orb(140, 151, 27, c) + _horizon(c, 313) + bridge
            + _tree(51, 345, c, 1.1) + _tree(229, 345, c, 1.1)
            + _figure(94, 346, c, 1.30, robe=c.mid, arms="open")
            + _figure(187, 346, c, 1.30, facing=-1, robe=c.light, arms="open")
            + _p("M125 281Q140 271 155 281", stroke=c.gold, width=2)
            + _p("M140 389Q127 356 139 337Q150 321 142 305", stroke=c.gold, width=1.8)
            + _star(140, 222, 12, c)
            + _flower(49, 329, c, .6) + _flower(232, 325, c, .6))


def _major_7(c):
    canopy = (_p("M74 211L90 175L190 175L206 211Z", c.deep, c.gold, 1.8)
              + _p("M89 177Q140 153 191 177", stroke=c.gold, width=1.3)
              + _constellation(c, ((109, 186, 4), (140, 194, 5), (171, 186, 4))))
    chassis = (_p("M78 257H202L213 317H67Z", c.deep, c.gold, 1.7)
               + _p("M89 269H191M83 286H198", stroke=c.paper, width=.9)
               + _c(94, 324, 20, c.pale, c.deep, 2) + _c(186, 324, 20, c.pale, c.deep, 2)
               + _c(94, 324, 7, c.gold) + _c(186, 324, 7, c.gold))
    return (_horizon(c, 313) + _p("M123 320L76 414M157 320L202 414", stroke=c.gold, width=1.7)
            + canopy + _figure(140, 276, c, .95, robe=c.mid)
            + chassis + _horse(68, 366, c, .75, -1, c.light)
            + _horse(214, 366, c, .75, 1, c.mid)
            + _p("M107 296Q97 325 70 335M173 296Q186 321 209 335",
                 stroke=c.gold, width=1.1))


def _major_8(c):
    loop = _p("M111 139C88 119 82 168 112 151C137 136 143 133 168 151"
              "C198 168 192 119 169 139C146 160 134 160 111 139Z",
              stroke=c.gold, width=2.5)
    return (_orb(140, 205, 52, c) + _horizon(c, 340)
            + _lion(101, 343, c, 1.25) + _figure(187, 351, c, 1.39, robe=c.light,
                                                facing=-1, arms="point")
            + _p("M167 295Q147 270 124 273", stroke=c.gold, width=3)
            + loop + _flower(52, 338, c, .7) + _flower(230, 338, c, .7)
            + _ground(c, 358))


def _major_9(c):
    lamp = (_p("M-13 -17L0 -31L13 -17V13H-13Z", c.light, c.deep, 1.6)
            + _r(-9, -15, 18, 24, c.gold, c.deep, 1)
            + _star(0, -3, 7, c)
            + _p("M-17 13H17M0 -31V-37", stroke=c.gold, width=1.7))
    return (_mountains(c, 302) + _p("M27 387Q47 359 76 346Q106 349 122 317"
                                    "Q150 283 180 295Q210 270 256 262", stroke=c.gold, width=3)
            + _p("M24 414L77 349L119 336L153 347L256 283V414Z", c.deep)
            + _figure(146, 314, c, 1.35, robe=c.mid)
            + _g(lamp, "translate(105 228) scale(1.2)")
            + _staff(193, 282, c, 1.2)
            + _p("M54 335L79 323M70 358L105 347M202 303L228 290",
                 stroke=c.paper, width=1.2)
            + _constellation(c, ((56, 161, 4), (217, 126, 5), (194, 193, 3))))


def _major_10(c):
    streamers = "".join(_p(f"M{sx} {sy}Q{cx} {cy} {ex} {ey}", stroke=c.gold, width=1.1,
                           extra='opacity=".76"') for sx, sy, cx, cy, ex, ey in
                        ((24, 219, 65, 150, 74, 184), (256, 220, 220, 177, 214, 203),
                         (24, 327, 55, 276, 74, 301), (256, 344, 208, 303, 214, 285)))
    return (_horizon(c, 329) + streamers + _wheel(140, 239, 83, c)
            + _constellation(c, ((52, 150, 8), (229, 151, 8),
                                 (52, 344, 8), (229, 344, 8)))
            + _p("M46 167q-8 10 -1 22M225 169q9 10 1 22M43 322q-9 -9 1 -20"
                 "M226 320q8 -8 0 -18", stroke=c.deep, width=1.3)
            + _star(140, 239, 8, c))


def _major_11(c):
    pan = (_p("M-70 -12H70M-58 -12V32M58 -12V32", stroke=c.gold, width=2)
           + _p("M-82 33Q-59 58 -36 33ZM36 33Q59 58 82 33Z", c.light, c.deep, 1.2))
    return (_arch(140, 151, 192, 205, c, filled=True)
            + _r(48, 255, 20, 101, c.deep, c.gold, 1)
            + _r(212, 255, 20, 101, c.deep, c.gold, 1)
            + _platform(c, 350)
            + _figure(140, 339, c, 1.22, robe=c.mid)
            + _g(pan, "translate(140 252)")
            + _sword(140, 214, c, 1.18)
            + _star(140, 123, 9, c)
            + _p("M47 355H233", stroke=c.gold, width=1))


def _major_12(c):
    halo = (_c(140, 289, 37, c.light, c.gold, 2)
            + _c(140, 289, 48, "none", c.gold, .8))
    body = (_p("M132 184L147 184L156 207L151 250Q141 263 126 250L121 209Z",
               c.mid, c.deep, 1.5)
            + _p("M132 248L128 269M149 248L152 268", stroke=c.deep, width=5)
            + _c(140, 288, 13, c.pale, c.deep, 1.5)
            + _p("M128 287Q126 275 137 271Q153 271 153 287", c.deep)
            + _p("M122 212Q100 228 99 246M156 211Q177 230 178 245",
                 stroke=c.deep, width=4)
            + _p("M130 193L125 161M150 193L155 160", stroke=c.gold, width=2))
    return (_mountains(c, 336, near=False)
            + _p("M24 160H256", stroke=c.deep, width=8)
            + _tree(68, 224, c, .75, bare=True) + _tree(227, 221, c, .72, bare=True)
            + _p("M114 160H167", stroke=c.gold, width=2)
            + halo + body
            + _p("M45 348Q140 332 235 348", stroke=c.gold, width=1.7)
            + _p("M62 330L140 414L218 330", stroke=c.mid, width=1))


def _major_13(c):
    gate = (_arch(140, 180, 178, 170, c, filled=True)
            + _arch(140, 204, 126, 148, c)
            + _p("M48 243L79 242M201 242L231 243M48 272L78 271"
                 "M202 271L231 272M51 299L80 299M201 299L229 299",
                 stroke=c.mid, width=1.15)
            + _p("M67 227L80 214M199 214L212 227M83 188L100 177"
                 "M180 177L197 188", stroke=c.gold, width=1.05)
            + _star(65, 208, 4, c) + _star(214, 208, 4, c))
    cloak = (_p("M97 350Q94 270 125 240Q149 225 171 245Q194 276 187 350Z",
                c.deep, c.gold, 1.2)
             + _p("M123 256Q141 243 157 256L164 287L140 305L115 286Z",
                  c.mid, c.deep, 1.4)
             + _p("M131 270Q143 263 152 270M128 280H153", stroke=c.paper, width=.9))
    shoot = _p("M201 365Q195 337 205 321M204 339Q218 324 227 329"
               "M202 348Q190 330 183 333", stroke=c.gold, width=2.5)
    return (_mountains(c, 320, near=False) + gate + _orb(142, 258, 32, c)
            + _platform(c, 351) + cloak
            + _staff(193, 298, c, 1.1, 13)
            + _p("M186 221Q219 225 221 257", stroke=c.deep, width=2)
            + _ground(c, 357) + shoot
            + _p("M38 340Q56 324 68 339M44 379Q92 367 119 380"
                 "M158 380Q182 367 241 381", stroke=c.gold, width=1)
            + _flower(52, 354, c, .32)
            + _p("M231 356q-10 9 -14 7M64 359q8 8 14 5", stroke=c.light, width=1.25))


def _major_14(c):
    flow = (_p("M92 264Q116 243 143 277Q164 295 190 259", stroke=c.gold, width=6)
            + _p("M93 264Q122 258 145 285Q170 304 191 261", stroke=c.paper, width=1))
    wings = (_p("M125 236Q75 219 70 171Q105 179 132 213Z", c.light, c.gold, 1.1)
             + _p("M155 236Q205 219 210 171Q175 179 148 213Z", c.light, c.gold, 1.1))
    return (_orb(140, 154, 24, c) + _water(c, 319, 5)
            + _p("M24 334Q63 302 113 322M164 328Q204 293 256 330", c.mid)
            + wings + _figure(140, 318, c, 1.23, robe=c.pale, arms="open")
            + _cup(89, 266, c, .85) + _cup(191, 264, c, .85) + flow
            + _p("M121 348Q140 338 159 347", stroke=c.gold, width=1.4)
            + _grass(46, 360, c, .7) + _grass(227, 351, c, .75))


def _major_15(c):
    shadow = (_p("M66 218L88 170L119 179L140 154L161 179L192 170L214 218"
                 "L186 321H94Z", c.deep, c.gold, 1.8)
              + _p("M94 189L78 144L112 178M186 189L202 144L168 178",
                   c.deep, c.gold, 1.4)
              + _c(116, 225, 4, c.gold) + _c(164, 225, 4, c.gold)
              + _p("M121 251Q140 265 159 251", stroke=c.gold, width=1.7))
    # The near links stop short: the attachment is real, but release is visible.
    links = "".join(_p(f"M{x+3} -6A7 7 0 1 0 {x+6} 2", stroke=c.gold, width=2)
                    for x in (0, 13, 26))
    chain_left = _g(links, "translate(65 328) rotate(-18)")
    chain_right = _g(links, "translate(185 329) rotate(18)")
    return (_arch(140, 151, 204, 208, c, filled=True)
            + _orb(140, 192, 27, c, moon=True) + shadow
            + _figure(73, 367, c, .66, robe=c.mid) + _figure(208, 367, c, .66, robe=c.mid)
            + chain_left + chain_right
            + _p("M100 357Q113 328 121 322M180 357Q167 328 159 322",
                 stroke=c.gold, width=2.1)
            + _p("M136 349q-12 -23 4 -39q-1 23 13 32q-2 18 -17 7Z", c.gold))


def _major_16(c):
    bolt = _p("M189 94L145 187L169 181L119 264L132 209L109 214Z",
              c.gold, c.paper, 2)
    tower = (_p("M91 197L178 181L200 351H77Z", c.deep, c.gold, 1.8)
             + _p("M84 195L178 178L174 160L101 174Z", c.mid, c.gold, 1.5)
             + _r(117, 229, 20, 43, c.pale, c.gold, 1)
             + _r(159, 220, 19, 43, c.pale, c.gold, 1)
             + _p("M90 293L181 280M91 310L183 298", stroke=c.paper, width=.9))
    debris = (_p("M58 265l20 -14l6 22Z", c.mid, c.gold, 1)
              + _p("M211 247l20 5l-13 19Z", c.mid, c.gold, 1)
              + _p("M102 347l18 -18l17 22Z", c.mid, c.gold, 1))
    storm = (_p("M24 126Q59 100 89 125Q108 89 146 116Q191 86 222 120"
                "Q241 110 256 127V68H24Z", c.mid, c.deep, 1.4)
             + _p("M29 141Q74 117 108 138M172 128Q215 109 252 140",
                  stroke=c.gold, width=1)
             + "".join(_p(f"M{x} {y}l-7 15", stroke=c.mid, width=1.15)
                       for x, y in ((51, 171), (69, 198), (230, 174), (241, 214),
                                    (42, 253), (224, 292))))
    fractures = (_p("M101 238L114 249L104 260L120 270M177 271L165 286"
                    "L186 301L173 310", stroke=c.gold, width=1.4)
                 + _p("M103 331L94 350M182 314L198 349", stroke=c.paper, width=.8))
    return (storm + _mountains(c, 338, near=False) + tower + fractures + bolt + debris
            + _p("M71 299L52 319M221 279L244 300", stroke=c.gold, width=1.5)
            + _figure(55, 337, c, .47, robe=c.light, arms="open")
            + _figure(224, 335, c, .45, robe=c.light, arms="open")
            + _ground(c, 352) + _star(58, 159, 7, c)
            + _p("M41 373l25 -12l18 13M185 379l26 -17l34 16", stroke=c.gold, width=1.2))


def _major_17(c):
    stars = _constellation(c, ((140, 142, 17), (66, 172, 6), (91, 205, 5),
                               (201, 181, 6), (224, 220, 5), (55, 235, 4),
                               (174, 213, 5), (113, 190, 4)))
    streams = (_p("M98 305Q89 327 62 354", stroke=c.gold, width=4)
               + _p("M178 307Q203 315 223 336", stroke=c.gold, width=4))
    return (stars + _water(c, 324, 5)
            + _p("M24 328Q65 303 120 317", c.mid)
            + _figure(140, 325, c, 1.1, robe=c.light, arms="open")
            + _cup(93, 299, c, .75) + _cup(188, 300, c, .75)
            + streams + _grass(44, 357, c, .8) + _grass(239, 348, c, .8)
            + _flower(49, 339, c, .55))


def _major_18(c):
    towers = (_r(45, 223, 42, 116, c.mid, c.deep, 1.4)
              + _r(193, 223, 42, 116, c.mid, c.deep, 1.4)
              + _p("M42 223L66 195L91 223M190 223L214 195L239 223",
                   c.deep, c.gold, 1.3)
              + _r(59, 254, 13, 28, c.pale, c.gold, 1)
              + _r(208, 254, 13, 28, c.pale, c.gold, 1))
    animals = (_p("M75 342Q80 312 94 307L104 317L116 310L124 339Z",
                  c.deep, c.gold, 1.3)
               + _p("M200 342Q197 312 184 309L172 319L163 311L155 339Z",
                    c.deep, c.gold, 1.3)
               + _c(104, 323, 2, c.gold) + _c(175, 322, 2, c.gold))
    path = _p("M121 414Q170 351 142 330Q111 309 142 284Q158 271 138 254",
              stroke=c.gold, width=3)
    night_marks = (_p("M33 122Q74 110 96 130M176 116Q213 109 252 130"
                      "M29 140Q62 127 83 139M201 136Q222 126 250 140",
                      stroke=c.mid, width=1.15)
                   + _p("M63 181q-5 11 0 18q6 -8 0 -18Z"
                        "M224 171q-5 11 0 18q6 -8 0 -18Z", c.gold)
                   + _constellation(c, ((52, 113, 3), (83, 89, 4),
                                        (219, 93, 4), (243, 165, 3))))
    return (night_marks + _orb(140, 163, 34, c, moon=True)
            + _horizon(c, 312) + towers + path + animals
            + _constellation(c, ((93, 161, 4), (212, 157, 4), (80, 201, 3)))
            + _water(c, 355, 2) + _c(140, 362, 7, "none", c.gold, 1)
            + _p("M42 248L49 245M79 247L86 250M198 247L207 245"
                 "M229 247L238 249", stroke=c.paper, width=.7))


def _major_19(c):
    sun = _orb(140, 169, 49, c)
    petals = "".join(_flower(x, y, c, s) for x, y, s in
                      ((44, 293, 1), (68, 276, .8), (211, 274, .9),
                       (233, 309, 1.05), (58, 339, .9), (218, 341, .83)))
    stems = "".join(_p(f"M{x} {y}v{347-y}", stroke=c.gold, width=1.5)
                    for x, y in ((44, 303), (68, 285), (211, 282), (233, 319),
                                 (58, 347), (218, 347)))
    return (sun + _horizon(c, 320)
            + _horse(144, 348, c, 1.15, -1, c.light)
            + _figure(139, 286, c, .8, robe=c.pale, arms="open")
            + _p("M42 259Q140 231 239 258", stroke=c.gold, width=1.5)
            + stems + petals + _ground(c, 355)
            + _p("M71 333Q87 322 101 330M182 330Q198 321 210 329",
                 stroke=c.paper, width=1))


def _major_20(c):
    trumpet = (_p("M105 173L163 198L163 220L105 195Z", c.gold, c.deep, 1.3)
               + _p("M163 208L215 222M104 185L89 178", stroke=c.gold, width=4))
    coffers = "".join(_r(x - 24, 332, 48, 32, c.mid, c.deep, 1.2)
                      + _p(f"M{x-25} 334Q{x} 323 {x+25} 334", stroke=c.gold, width=1.2)
                      for x in (62, 140, 218))
    return (_orb(141, 147, 27, c) + _horizon(c, 326)
            + _figure(139, 231, c, 1.06, robe=c.light, arms="open")
            + trumpet + _p("M78 204L48 256M206 208L234 256M140 213V281",
                           stroke=c.gold, width=1.3)
            + coffers + "".join(_figure(x, 335, c, .65, robe=c.pale, arms="up")
                                   for x in (62, 140, 218))
            + _platform(c, 362))


def _major_21(c):
    wreath = (_p("M125 150A92 92 0 1 0 156 150", stroke=c.gold, width=4)
              + _p("M126 160A82 82 0 1 0 155 160", stroke=c.mid, width=1.5))
    leaves = "".join(_g(_p("M0 0Q-13 -8 -12 -21Q2 -16 0 0Z", c.mid, c.gold, .7),
                         f"translate({140 + math.cos(math.radians(a))*92:.1f} "
                         f"{241 + math.sin(math.radians(a))*92:.1f}) rotate({a+90})")
                     for a in range(0, 360, 22))
    witnesses = "".join(_c(x, y, 15, c.pale, c.gold, 1.4)
                        for x, y in ((47, 151), (233, 151), (47, 337), (233, 337)))
    witnesses += (_p("M39 151l9 -8l7 8l-7 7Z", c.mid, c.deep, 1)
                  + _p("M224 150l8 -8l9 8l-8 9Z", c.mid, c.deep, 1)
                  + _p("M41 341l6 -10l6 10Z", c.mid, c.deep, 1)
                  + _p("M226 342q6 -15 14 0Z", c.mid, c.deep, 1))
    dancer = (_figure(140, 303, c, 1.34, robe=c.light, arms="open")
              + _p("M139 298Q120 323 109 333M143 299Q161 319 174 331",
                   stroke=c.deep, width=4)
              + _p("M100 237Q126 251 136 266M180 232Q157 251 147 267",
                   stroke=c.gold, width=2.2))
    return (_orb(140, 242, 59, c) + wreath + leaves + dancer + witnesses
            + _p("M63 360Q140 335 217 360", stroke=c.gold, width=1.4))


_SCENES = (
    _major_0, _major_1, _major_2, _major_3, _major_4, _major_5,
    _major_6, _major_7, _major_8, _major_9, _major_10, _major_11,
    _major_12, _major_13, _major_14, _major_15, _major_16, _major_17,
    _major_18, _major_19, _major_20, _major_21,
)


def render_major(card: dict, palette) -> str:
    """Return a complete, original theme-aware Major Arcana illustration."""
    number = card["number"]
    if card["arcana"] != "major" or not 0 <= number < len(_SCENES):
        raise ValueError(f"Not a Major Arcana card: {card.get('id')}")
    colors = _Colors(palette, number)
    night = number in {2, 9, 12, 15, 17, 18}
    return _sky(number, colors, night=night) + _SCENES[number](colors)
