"""Lush, cartoon golf-course background as horizontally tileable parallax layers (SVG).

Writes <out>/svg/layer_*.svg, <out>/svg/background_full.svg.
Each SVG is a 1920x1920 square canvas with the 1920x1080 scene centered vertically
(offset 420) so macOS quicklook can render it; crop the middle 1080 rows afterwards.
"""
import math
import os
import random
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "golf_background"
os.makedirs(os.path.join(OUT, "svg"), exist_ok=True)
W, H = 1920, 1080
INK = "#1d3a2a"            # soft dark-green outline (friendlier than black for nature)
SKY_TOP, SKY_BOTTOM = "#5ec8ff", "#d9f7ff"


def wave(x, base, terms):
    return base + sum(a * math.sin(2 * math.pi * k * x / W + p) for a, k, p in terms)


def hill_path(base, terms, step=16):
    pts = [(x, wave(x, base, terms)) for x in range(0, W + step, step)]
    return f"M0 {H} " + " ".join(f"L{x} {y:.1f}" for x, y in pts) + f" L{W} {H} Z"


def ridge(base, terms, sw, step=16):
    pts = [(x, wave(x, base, terms)) for x in range(-step, W + 2 * step, step)]
    d = "M" + " L".join(f"{x} {y:.1f}" for x, y in pts)
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'


def wrap(x, draw):
    """Draw an element at x and its copies one screen-width away, so the layer tiles."""
    return "".join(draw(x + dx) for dx in (-W, 0, W))


def blob(circles, fill, stroke=INK, sw=5):
    """Outlined cartoon blob: outlined circles first, then fills on top to hide inner seams."""
    out = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw*2}"/>'
                  for x, y, r in circles) if stroke else ""
    out += "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>' for x, y, r in circles)
    return out


# ------------------------------------------------------------------ layers
def layer_sky():
    rnd = random.Random(1)
    s = ('<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="{SKY_TOP}"/><stop offset="1" stop-color="{SKY_BOTTOM}"/></linearGradient>'
         '<radialGradient id="glow"><stop offset="0" stop-color="#fff7c2" stop-opacity="0.9"/>'
         '<stop offset="1" stop-color="#fff7c2" stop-opacity="0"/></radialGradient></defs>'
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
         '<circle cx="1560" cy="190" r="230" fill="url(#glow)"/>'
         f'<circle cx="1560" cy="190" r="86" fill="#ffe066" stroke="#f5b82e" stroke-width="8"/>'
         '<circle cx="1534" cy="166" r="26" fill="#fff3a8"/>')
    for i in range(7):
        x, y, sc = i * W / 7 + rnd.uniform(0, 120), rnd.uniform(90, 380), rnd.uniform(0.7, 1.25)
        if 1250 < x < 1760:
            y = rnd.uniform(400, 440)
        parts = [(0, 0, 46), (52, -18, 58), (110, 0, 44), (58, 14, 46), (-34, 12, 32), (144, 14, 30)]
        s += wrap(x, lambda X, y=y, sc=sc: blob([(X + a * sc, y + b * sc, r * sc) for a, b, r in parts],
                                                "#ffffff", stroke="#a9dff5", sw=3))
    return s


def layer_mountains():
    terms = [(70, 1, 0.4), (45, 3, 1.9), (22, 7, 0.3)]
    s = f'<path d="{hill_path(560, terms)}" fill="#9fdcc0"/>'
    terms2 = [(55, 2, 2.2), (30, 5, 0.9), (14, 11, 1.4)]
    s += f'<path d="{hill_path(640, terms2)}" fill="#7ccfa2"/>'
    return s


def layer_hills():
    rnd = random.Random(2)
    terms = [(40, 2, 0.8), (22, 5, 2.6), (8, 13, 0.2)]
    s = f'<path d="{hill_path(700, terms)}" fill="#55c36b"/>' + ridge(700, terms, 5)
    # distant round trees along the ridge
    for i in range(34):
        x = i * W / 34 + rnd.uniform(-15, 15)
        y = wave(x, 700, terms) + 6
        r = rnd.uniform(16, 26)
        shade = rnd.choice(["#3fae58", "#36a050", "#48b960"])
        s += wrap(x, lambda X, y=y, r=r, c=shade: blob([(X, y - r, r), (X - r * .7, y - r * .5, r * .7), (X + r * .7, y - r * .5, r * .7)], c, sw=3))
    # little flag on the green
    fx = 1180
    fy = wave(fx, 700, terms)
    s += (f'<ellipse cx="{fx}" cy="{fy+4:.1f}" rx="70" ry="14" fill="#7ee08a" stroke="{INK}" stroke-width="4"/>'
          f'<line x1="{fx}" y1="{fy+2:.1f}" x2="{fx}" y2="{fy-96:.1f}" stroke="#f4f4f4" stroke-width="6" stroke-linecap="round"/>'
          f'<line x1="{fx}" y1="{fy+2:.1f}" x2="{fx}" y2="{fy-96:.1f}" stroke="{INK}" stroke-width="2"/>'
          f'<path d="M{fx+2} {fy-96:.1f} L{fx+58} {fy-80:.1f} L{fx+2} {fy-62:.1f} Z" fill="#ff4d5e" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    return s


def round_tree(X, y, h, canopy, trunk="#8a5a32"):
    tw = h * 0.12
    s = f'<rect x="{X-tw/2:.1f}" y="{y-h*0.55:.1f}" width="{tw:.1f}" height="{h*0.58:.1f}" rx="{tw/3:.1f}" fill="{trunk}" stroke="{INK}" stroke-width="5"/>'
    r = h * 0.32
    s += blob([(X, y - h * 0.82, r), (X - r * .8, y - h * 0.62, r * .8), (X + r * .8, y - h * 0.64, r * .82),
               (X, y - h * 0.58, r * .75)], canopy)
    s += f'<circle cx="{X - r*0.35:.1f}" cy="{y - h*0.9:.1f}" r="{r*0.28:.1f}" fill="#ffffff" opacity="0.18"/>'
    return s


def pine_tree(X, y, h, c1, c2):
    s = f'<rect x="{X-h*0.05:.1f}" y="{y-h*0.2:.1f}" width="{h*0.1:.1f}" height="{h*0.22:.1f}" fill="#7a4b28" stroke="{INK}" stroke-width="5"/>'
    for i, (wf, top, bot) in enumerate(((0.42, 0.55, 0.12), (0.34, 0.80, 0.38), (0.24, 1.0, 0.62))):
        c = c1 if i % 2 == 0 else c2
        s += (f'<path d="M{X-h*wf:.1f} {y-h*bot:.1f} L{X:.1f} {y-h*top:.1f} L{X+h*wf:.1f} {y-h*bot:.1f} Z" '
              f'fill="{c}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    return s


def layer_trees():
    rnd = random.Random(3)
    terms = [(26, 3, 1.1), (12, 7, 0.4)]
    s = f'<path d="{hill_path(790, terms)}" fill="#3fb45a"/>' + ridge(790, terms, 5)
    xs = sorted(x for x in (rnd.uniform(0, W) for _ in range(26)) if not 960 < x < 1420)[:15]
    for x in xs:
        y = wave(x, 790, terms) + 10
        h = rnd.uniform(110, 185)
        if rnd.random() < 0.35:
            s += wrap(x, lambda X, y=y, h=h: pine_tree(X, y, h, "#1f8a45", "#26a052"))
        else:
            c = rnd.choice(["#2ea84e", "#249344", "#38b85a"])
            s += wrap(x, lambda X, y=y, h=h, c=c: round_tree(X, y, h, c))
    return s


def layer_ground():
    rnd = random.Random(4)
    terms = [(10, 2, 0.5), (5, 5, 1.7)]
    top = 880
    s = (f'<clipPath id="grd"><path d="{hill_path(top, terms)}"/></clipPath>'
         f'<path d="{hill_path(top, terms)}" fill="#6fd66f"/>'
         '<g clip-path="url(#grd)" opacity="0.5">')
    stripe = W / 12   # 12 stripes -> tiles cleanly
    for i in range(-2, 14):
        if i % 2 == 0:
            x = i * stripe
            s += f'<path d="M{x:.1f} {top-40} L{x+stripe:.1f} {top-40} L{x+stripe+160:.1f} {H} L{x+160:.1f} {H} Z" fill="#8be58a"/>'
    s += '</g>'
    s += ridge(top, terms, 6)
    # bushes on the horizon line
    for i in range(9):
        x = i * W / 9 + rnd.uniform(0, 140)
        y = wave(x, top, terms) + 8
        r = rnd.uniform(26, 40)
        s += wrap(x, lambda X, y=y, r=r: blob([(X, y - r * .6, r), (X - r, y - r * .2, r * .75), (X + r, y - r * .25, r * .8)], "#2fa44f"))
    # flowers, grass tufts, pebbles
    for _ in range(70):
        x, y = rnd.uniform(0, W), rnd.uniform(top + 30, H - 20)
        kind = rnd.random()
        if kind < 0.45:
            c = rnd.choice(["#ffffff", "#ffe14d", "#ff8fc7", "#ff6b6b", "#b98cff"])
            s += wrap(x, lambda X, y=y, c=c: "".join(
                f'<circle cx="{X+6*math.cos(a):.1f}" cy="{y+6*math.sin(a):.1f}" r="5" fill="{c}" stroke="{INK}" stroke-width="2"/>'
                for a in (0, 1.257, 2.513, 3.77, 5.027)) + f'<circle cx="{X:.1f}" cy="{y:.1f}" r="4" fill="#ffb02e"/>')
        elif kind < 0.9:
            s += wrap(x, lambda X, y=y: f'<path d="M{X-10:.1f} {y:.1f} L{X-4:.1f} {y-18:.1f} L{X:.1f} {y:.1f} L{X+5:.1f} {y-22:.1f} L{X+11:.1f} {y:.1f}" '
                                        f'fill="none" stroke="#3aa955" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
        else:
            s += wrap(x, lambda X, y=y: f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="14" ry="9" fill="#c9cfc4" stroke="{INK}" stroke-width="3"/>')
    return s


LAYERS = [("01_sky", layer_sky()), ("02_mountains", layer_mountains()), ("03_hills", layer_hills()),
          ("04_trees", layer_trees()), ("05_ground", layer_ground())]


def doc(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">'
            f'<defs><clipPath id="frame"><rect width="{W}" height="{H}"/></clipPath></defs>'
            f'<g transform="translate(0 420)"><g clip-path="url(#frame)">{body}</g></g></svg>')


for name, body in LAYERS:
    with open(os.path.join(OUT, "svg", f"layer_{name}.svg"), "w") as f:
        f.write(doc(body))
with open(os.path.join(OUT, "svg", "background_full.svg"), "w") as f:
    f.write(doc("".join(b for _, b in LAYERS)))
print("ok")
