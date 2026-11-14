"""Six connected, side-scrolling golf backgrounds (zone 1 = the original meadow).

Each zone's right edge flows seamlessly into the next zone's left edge, layer by layer:
  * terrain lines share the same base curve at the edges (zone variation fades out near edges)
  * any element cut off by a zone's right edge continues on the next zone's left edge

Usage: python3 make_golf_zones.py <out_dir>
Writes <out>/zone_0N_<name>/svg/{layer_01_sky..layer_05_ground,background_full}.svg
(1920x1920 square canvas, scene in rows 420..1500; crop the middle 1080 rows after rendering)
and <out>/zones_preview.svg.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zone_palette import PALETTE, N_ZONES, hgrad  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "golf_background"
SIGNS = "--no-signs" not in sys.argv   # the game draws its own flag markers, so it renders ground layers without signs
W, H = 1920, 1080
INK = "#1d3a2a"
SKY_TOP, SKY_BOTTOM = "#5ec8ff", "#d9f7ff"

# ======================================================================= shared helpers (zone 1 identical)
REC = []   # elements recorded by wrap() for the zone-1 layer being built: (x, ext, draw)


def wave(x, base, terms):
    return base + sum(a * math.sin(2 * math.pi * k * x / W + p) for a, k, p in terms)


def hill_path(base, terms, step=16):
    pts = [(x, wave(x, base, terms)) for x in range(0, W + step, step)]
    return f"M0 {H} " + " ".join(f"L{x} {y:.1f}" for x, y in pts) + f" L{W} {H} Z"


def ridge(base, terms, sw, step=16):
    pts = [(x, wave(x, base, terms)) for x in range(-step, W + 2 * step, step)]
    d = "M" + " L".join(f"{x} {y:.1f}" for x, y in pts)
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'


def wrap(x, draw, ext=0):
    REC.append((x, ext, draw))
    return "".join(draw(x + dx) for dx in (-W, 0, W))


def blob(circles, fill, stroke=INK, sw=5):
    out = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw*2}"/>'
                  for x, y, r in circles) if stroke else ""
    out += "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>' for x, y, r in circles)
    return out


CLOUD_PARTS = [(0, 0, 46), (52, -18, 58), (110, 0, 44), (58, 14, 46), (-34, 12, 32), (144, 14, 30)]


def cloud(X, y, sc):
    return blob([(X + a * sc, y + b * sc, r * sc) for a, b, r in CLOUD_PARTS], "#ffffff", stroke="#a9dff5", sw=3)


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


def flower(X, y, c):
    return ("".join(f'<circle cx="{X+6*math.cos(a):.1f}" cy="{y+6*math.sin(a):.1f}" r="5" fill="{c}" stroke="{INK}" stroke-width="2"/>'
                    for a in (0, 1.257, 2.513, 3.77, 5.027)) + f'<circle cx="{X:.1f}" cy="{y:.1f}" r="4" fill="#ffb02e"/>')


def tuft(X, y):
    return (f'<path d="M{X-10:.1f} {y:.1f} L{X-4:.1f} {y-18:.1f} L{X:.1f} {y:.1f} L{X+5:.1f} {y-22:.1f} L{X+11:.1f} {y:.1f}" '
            f'fill="none" stroke="#3aa955" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')


def pebble(X, y):
    return f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="14" ry="9" fill="#c9cfc4" stroke="{INK}" stroke-width="3"/>'


def bush(X, y, r, c="#2fa44f"):
    return blob([(X, y - r * .6, r), (X - r, y - r * .2, r * .75), (X + r, y - r * .25, r * .8)], c)


def sky_defs(zone):
    # sky colour (blended across seams) with a white haze toward the horizon
    return ('<defs>' + hgrad("skyc", zone, "sky") +
            '<linearGradient id="skyfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#ffffff" stop-opacity="0.68"/></linearGradient>'
            '<radialGradient id="glow"><stop offset="0" stop-color="#fff7c2" stop-opacity="0.9"/>'
            '<stop offset="1" stop-color="#fff7c2" stop-opacity="0"/></radialGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#skyc)"/><rect width="{W}" height="{H}" fill="url(#skyfade)"/>')


def layer_defs(zone, *pairs):
    return "<defs>" + "".join(hgrad(gid, zone, key) for gid, key in pairs) + "</defs>"


# Base terrain of every layer (identical in all zones at the edges)
T_MTN_BACK = (560, [(70, 1, 0.4), (45, 3, 1.9), (22, 7, 0.3)])
T_MTN_FRONT = (640, [(55, 2, 2.2), (30, 5, 0.9), (14, 11, 1.4)])
T_HILLS = (700, [(40, 2, 0.8), (22, 5, 2.6), (8, 13, 0.2)])
T_TREES = (790, [(26, 3, 1.1), (12, 7, 0.4)])
T_GROUND = (880, [(10, 2, 0.5), (5, 5, 1.7)])


# ======================================================================= zone 1 (original meadow, unchanged output)
def z1_sky():
    rnd = random.Random(1)
    s = (sky_defs(1) +
         '<circle cx="1560" cy="190" r="230" fill="url(#glow)"/>'
         f'<circle cx="1560" cy="190" r="86" fill="#ffe066" stroke="#f5b82e" stroke-width="8"/>'
         '<circle cx="1534" cy="166" r="26" fill="#fff3a8"/>')
    for i in range(4):
        x, y, sc = i * W / 4 + rnd.uniform(0, 160), rnd.uniform(90, 380), rnd.uniform(0.8, 1.25)
        if 1250 < x < 1760:
            y = rnd.uniform(400, 440)
        s += wrap(x, lambda X, y=y, sc=sc: cloud(X, y, sc), ext=182 * sc)
    return s


def z1_mountains():
    s = layer_defs(1, ("mb", "mb"), ("mf", "mf"))
    s += f'<path d="{hill_path(*T_MTN_BACK)}" fill="url(#mb)"/>'
    s += f'<path d="{hill_path(*T_MTN_FRONT)}" fill="url(#mf)"/>'
    return s


def z1_hills():
    rnd = random.Random(2)
    base, terms = T_HILLS
    s = layer_defs(1, ("hl", "hills")) + f'<path d="{hill_path(base, terms)}" fill="url(#hl)"/>' + ridge(base, terms, 5)
    for i in range(14):
        x = i * W / 14 + rnd.uniform(-25, 25)
        y = wave(x, base, terms) + 6
        r = rnd.uniform(16, 26)
        shade = rnd.choice(["#3fae58", "#36a050", "#48b960"])
        s += wrap(x, lambda X, y=y, r=r, c=shade: blob([(X, y - r, r), (X - r * .7, y - r * .5, r * .7), (X + r * .7, y - r * .5, r * .7)], c, sw=3),
                  ext=r * 1.7 + 4)
    fx = 1180
    fy = wave(fx, base, terms)
    s += (f'<ellipse cx="{fx}" cy="{fy+4:.1f}" rx="70" ry="14" fill="#7ee08a" stroke="{INK}" stroke-width="4"/>'
          f'<line x1="{fx}" y1="{fy+2:.1f}" x2="{fx}" y2="{fy-96:.1f}" stroke="#f4f4f4" stroke-width="6" stroke-linecap="round"/>'
          f'<line x1="{fx}" y1="{fy+2:.1f}" x2="{fx}" y2="{fy-96:.1f}" stroke="{INK}" stroke-width="2"/>'
          f'<path d="M{fx+2} {fy-96:.1f} L{fx+58} {fy-80:.1f} L{fx+2} {fy-62:.1f} Z" fill="#ff4d5e" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    return s


def z1_trees():
    rnd = random.Random(3)
    base, terms = T_TREES
    s = layer_defs(1, ("tr", "trees")) + f'<path d="{hill_path(base, terms)}" fill="url(#tr)"/>' + ridge(base, terms, 5)
    xs = sorted(x for x in (rnd.uniform(0, W) for _ in range(26)) if not 960 < x < 1420)[:9]
    for x in xs:
        y = wave(x, base, terms) + 10
        h = rnd.uniform(110, 185)
        if rnd.random() < 0.35:
            s += wrap(x, lambda X, y=y, h=h: pine_tree(X, y, h, "#1f8a45", "#26a052"), ext=h * 0.42 + 5)
        else:
            c = rnd.choice(["#2ea84e", "#249344", "#38b85a"])
            s += wrap(x, lambda X, y=y, h=h, c=c: round_tree(X, y, h, c), ext=h * 0.56 + 5)
    return s


def ground_base(yf=None, zone=1):
    base, terms = T_GROUND
    top = base
    if yf is None:
        path, rid = hill_path(base, terms), ridge(top, terms, 6)
    else:
        path, rid = gpath(yf), gridge(yf, 6)
    s = (layer_defs(zone, ("gd", "ground"), ("gs", "stripe")) +
         f'<clipPath id="grd"><path d="{path}"/></clipPath>'
         f'<path d="{path}" fill="url(#gd)"/>'
         '<g clip-path="url(#grd)" opacity="0.5">')
    stripe = W / 12
    for i in range(-2, 14):
        if i % 2 == 0:
            x = i * stripe
            s += f'<path d="M{x:.1f} {top-40} L{x+stripe:.1f} {top-40} L{x+stripe+160:.1f} {H} L{x+160:.1f} {H} Z" fill="url(#gs)"/>'
    s += '</g>' + rid
    return s


def z1_ground():
    rnd = random.Random(4)
    base, terms = T_GROUND
    s = ground_base()
    for i in range(5):
        x = i * W / 5 + rnd.uniform(0, 200)
        y = wave(x, base, terms) + 8
        r = rnd.uniform(26, 40)
        s += wrap(x, lambda X, y=y, r=r: bush(X, y, r), ext=r * 1.8 + 6)
    for _ in range(22):
        x, y = rnd.uniform(0, W), rnd.uniform(base + 30, H - 20)
        kind = rnd.random()
        if kind < 0.45:
            c = rnd.choice(["#ffffff", "#ffe14d", "#ff8fc7", "#ff6b6b", "#b98cff"])
            s += wrap(x, lambda X, y=y, c=c: flower(X, y, c), ext=13)
        elif kind < 0.9:
            s += wrap(x, lambda X, y=y: tuft(X, y), ext=13)
        else:
            s += wrap(x, lambda X, y=y: pebble(X, y), ext=17)
    return s


# ======================================================================= generic terrain for zones 2-6
def window(x):
    return math.sin(math.pi * x / W) ** 2


def make_yf(t, extra=(), lift=0.0):
    base, terms = t
    return lambda x: wave(x, base, terms) + window(x) * (lift + sum(a * math.sin(2 * math.pi * k * x / W + p) for a, k, p in extra))


def gpath(yf, step=16):
    return f"M0 {H} " + " ".join(f"L{x} {yf(x):.1f}" for x in range(0, W + step, step)) + f" L{W} {H} Z"


def gridge(yf, sw, step=16):
    d = "M" + " L".join(f"{x} {yf(x):.1f}" for x in range(-step, W + 2 * step, step))
    return f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{sw}" stroke-linejoin="round"/>'


# ----------------------------------------------------------------------- structure / nature drawings
STONE, STONE_D = "#e3d9bf", "#c4b796"
ROCK, ROCK_D = "#a3aca2", "#7f897f"


def boulder(X, y, w, h, c=ROCK, moss=False):
    s = (f'<path d="M{X-w/2:.1f} {y:.1f} Q{X-w*0.55:.1f} {y-h*0.7:.1f} {X-w*0.15:.1f} {y-h:.1f} '
         f'Q{X+w*0.3:.1f} {y-h*1.08:.1f} {X+w*0.48:.1f} {y-h*0.5:.1f} Q{X+w*0.58:.1f} {y-h*0.05:.1f} {X+w*0.42:.1f} {y:.1f} Z" '
         f'fill="{c}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
         f'<path d="M{X-w*0.28:.1f} {y-h*0.72:.1f} Q{X-w*0.12:.1f} {y-h*0.9:.1f} {X+w*0.12:.1f} {y-h*0.88:.1f}" fill="none" stroke="#ffffff" stroke-opacity="0.45" stroke-width="5" stroke-linecap="round"/>'
         f'<path d="M{X+w*0.12:.1f} {y-h*0.45:.1f} L{X+w*0.22:.1f} {y-h*0.25:.1f} L{X+w*0.15:.1f} {y-h*0.1:.1f}" fill="none" stroke="{ROCK_D}" stroke-width="3" stroke-linecap="round"/>')
    if moss:
        s += blob([(X - w * 0.2, y - h * 0.93, w * 0.16), (X + w * 0.02, y - h * 0.98, w * 0.14), (X + w * 0.22, y - h * 0.82, w * 0.11)], "#4cbf5f", sw=3)
    return s


def rock_arch(X, y, s):
    d = f"M{X-s:.1f} {y:.1f} L{X-s*0.85:.1f} {y-s*0.9:.1f} Q{X:.1f} {y-s*1.75:.1f} {X+s*0.85:.1f} {y-s*0.9:.1f} L{X+s:.1f} {y:.1f}"
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{s*0.42+10:.1f}" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{ROCK}" stroke-width="{s*0.42:.1f}" stroke-linejoin="round"/>'
            f'<path d="M{X-s*0.6:.1f} {y-s*1.2:.1f} Q{X:.1f} {y-s*1.62:.1f} {X+s*0.5:.1f} {y-s*1.25:.1f}" fill="none" stroke="#ffffff" stroke-opacity="0.4" stroke-width="5" stroke-linecap="round"/>'
            + blob([(X - s * 0.25, y - s * 1.5, s * 0.14), (X + s * 0.05, y - s * 1.56, s * 0.12)], "#4cbf5f", sw=3))


def cliff(X, y, w, h):
    s = ""
    for i, (fw, fh, c) in enumerate(((1.0, 0.45, ROCK_D), (0.8, 0.75, ROCK), (0.55, 1.0, "#b4bcb2"))):
        x0 = X - w * fw / 2 + i * w * 0.06
        s += (f'<path d="M{x0:.1f} {y:.1f} L{x0+w*0.05:.1f} {y-h*fh:.1f} L{x0+w*fw*0.85:.1f} {y-h*fh-6:.1f} L{x0+w*fw:.1f} {y:.1f} Z" '
              f'fill="{c}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    s += blob([(X - w * 0.12, y - h * 1.0, w * 0.09), (X + w * 0.08, y - h * 1.02, w * 0.08)], "#4cbf5f", sw=3)
    return s


def column(X, y, h, broken=False, w=34):
    s = (f'<rect x="{X-w*0.68:.1f}" y="{y-12:.1f}" width="{w*1.36:.1f}" height="14" rx="3" fill="{STONE_D}" stroke="{INK}" stroke-width="5"/>')
    top = y - h
    if broken:
        s += (f'<path d="M{X-w/2:.1f} {y-12:.1f} L{X-w/2:.1f} {top+18:.1f} L{X-w*0.2:.1f} {top+4:.1f} L{X:.1f} {top+16:.1f} '
              f'L{X+w*0.25:.1f} {top:.1f} L{X+w/2:.1f} {top+12:.1f} L{X+w/2:.1f} {y-12:.1f} Z" fill="{STONE}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    else:
        s += (f'<rect x="{X-w/2:.1f}" y="{top+14:.1f}" width="{w:.1f}" height="{h-26:.1f}" fill="{STONE}" stroke="{INK}" stroke-width="5"/>'
              f'<rect x="{X-w*0.72:.1f}" y="{top:.1f}" width="{w*1.44:.1f}" height="16" rx="3" fill="{STONE_D}" stroke="{INK}" stroke-width="5"/>')
    for fx in (-0.22, 0.0, 0.22):
        s += f'<line x1="{X+w*fx:.1f}" y1="{y-18:.1f}" x2="{X+w*fx:.1f}" y2="{top+24:.1f}" stroke="{STONE_D}" stroke-width="3"/>'
    return s


def stone_arch(X, y, w, h, t=36):
    r = w / 2
    d = (f"M{X-r:.1f} {y:.1f} L{X-r:.1f} {y-h+r:.1f} A{r:.1f} {r:.1f} 0 0 1 {X+r:.1f} {y-h+r:.1f} L{X+r:.1f} {y:.1f} "
         f"L{X+r-t:.1f} {y:.1f} L{X+r-t:.1f} {y-h+r:.1f} A{r-t:.1f} {r-t:.1f} 0 0 0 {X-r+t:.1f} {y-h+r:.1f} L{X-r+t:.1f} {y:.1f} Z")
    s = f'<path d="{d}" fill="{STONE}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
    cy = y - h + r
    for i in range(1, 8):
        a = math.pi * i / 8
        s += (f'<line x1="{X - (r-t)*math.cos(a):.1f}" y1="{cy - (r-t)*math.sin(a):.1f}" '
              f'x2="{X - r*math.cos(a):.1f}" y2="{cy - r*math.sin(a):.1f}" stroke="{STONE_D}" stroke-width="3"/>')
    for yy in range(int(y - 40), int(cy), -40):
        s += (f'<line x1="{X-r:.1f}" y1="{yy}" x2="{X-r+t:.1f}" y2="{yy}" stroke="{STONE_D}" stroke-width="3"/>'
              f'<line x1="{X+r-t:.1f}" y1="{yy}" x2="{X+r:.1f}" y2="{yy}" stroke="{STONE_D}" stroke-width="3"/>')
    s += f'<path d="M{X-r+8:.1f} {cy+30:.1f} Q{X-r-6:.1f} {cy+90:.1f} {X-r+10:.1f} {cy+150:.1f}" fill="none" stroke="#3aa955" stroke-width="5" stroke-linecap="round"/>'
    return s


def ruin_wall(X, y, w, h):
    bw, bh = 40, 22
    s = ""
    rows = int(h / bh)
    for r_ in range(rows):
        frac = 1 - r_ / rows
        rw = w * (0.45 + 0.55 * frac)
        x0 = X - w / 2
        off = (bw / 2) if r_ % 2 else 0
        xx = x0 - off
        while xx < x0 + rw:
            bx, bwid = max(xx, x0), min(xx + bw, x0 + rw) - max(xx, x0)
            if bwid > 4:
                s += (f'<rect x="{bx:.1f}" y="{y-(r_+1)*bh:.1f}" width="{bwid:.1f}" height="{bh}" '
                      f'fill="{STONE if (r_+int(xx/bw))%3 else STONE_D}" stroke="{INK}" stroke-width="3"/>')
            xx += bw
    return s


def ziggurat(X, y, w, h, steps=5, c="#c9bb8f", cd="#a99a6c"):
    s = ""
    sh = h / (steps + 0.8)
    for i in range(steps):
        sw_ = w * (1 - i * 0.16)
        yb = y - i * sh
        s += (f'<path d="M{X-sw_/2:.1f} {yb:.1f} L{X-sw_/2+sh*0.25:.1f} {yb-sh:.1f} L{X+sw_/2-sh*0.25:.1f} {yb-sh:.1f} L{X+sw_/2:.1f} {yb:.1f} Z" '
              f'fill="{c if i%2==0 else cd}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    st = w * 0.16
    s += f'<path d="M{X-st/2:.1f} {y:.1f} L{X-st/2+sh*steps*0.12:.1f} {y-sh*steps:.1f} L{X+st/2-sh*steps*0.12:.1f} {y-sh*steps:.1f} L{X+st/2:.1f} {y:.1f} Z" fill="{cd}" stroke="{INK}" stroke-width="4"/>'
    for i in range(1, int(steps * 3)):
        yy = y - i * sh / 3
        s += f'<line x1="{X-st/2+ i*2:.1f}" y1="{yy:.1f}" x2="{X+st/2- i*2:.1f}" y2="{yy:.1f}" stroke="{INK}" stroke-width="2" opacity="0.5"/>'
    ty = y - steps * sh
    tw = w * (1 - steps * 0.16) * 0.7
    s += (f'<rect x="{X-tw/2:.1f}" y="{ty-sh*0.8:.1f}" width="{tw:.1f}" height="{sh*0.8:.1f}" fill="{c}" stroke="{INK}" stroke-width="5"/>'
          f'<rect x="{X-tw*0.16:.1f}" y="{ty-sh*0.62:.1f}" width="{tw*0.32:.1f}" height="{sh*0.62:.1f}" rx="6" fill="#2a2333"/>')
    for vx in (-0.38, -0.22, 0.3, 0.41):
        x0 = X + w * vx
        s += f'<path d="M{x0:.1f} {y-h*0.62:.1f} Q{x0+10:.1f} {y-h*0.45:.1f} {x0-4:.1f} {y-h*0.25:.1f}" fill="none" stroke="#2f9e4f" stroke-width="5" stroke-linecap="round"/>'
        s += f'<circle cx="{x0-4:.1f}" cy="{y-h*0.25:.1f}" r="6" fill="#3fb45a" stroke="{INK}" stroke-width="2"/>'
    return s


def palm(X, y, h, lean=1):
    tx, ty = X + lean * h * 0.18, y - h
    s = (f'<path d="M{X:.1f} {y:.1f} Q{X+lean*h*0.02:.1f} {y-h*0.6:.1f} {tx:.1f} {ty:.1f}" fill="none" stroke="{INK}" stroke-width="{h*0.09+8:.1f}" stroke-linecap="round"/>'
         f'<path d="M{X:.1f} {y:.1f} Q{X+lean*h*0.02:.1f} {y-h*0.6:.1f} {tx:.1f} {ty:.1f}" fill="none" stroke="#a6743f" stroke-width="{h*0.09:.1f}" stroke-linecap="round"/>')
    for i in range(1, 8):
        t = i / 8
        px = (1 - t) ** 2 * X + 2 * (1 - t) * t * (X + lean * h * 0.02) + t * t * tx
        py = (1 - t) ** 2 * y + 2 * (1 - t) * t * (y - h * 0.6) + t * t * ty
        s += f'<line x1="{px-h*0.04:.1f}" y1="{py:.1f}" x2="{px+h*0.04:.1f}" y2="{py-4:.1f}" stroke="#7d5427" stroke-width="3"/>'
    for ang, ln in ((-160, 0.5), (-125, 0.55), (-90, 0.4), (-55, 0.55), (-20, 0.5), (15, 0.38), (-195, 0.38)):
        a = math.radians(ang)
        ex, ey = tx + math.cos(a) * h * ln, ty + math.sin(a) * h * ln * 0.6 + h * 0.12
        mx, my = tx + math.cos(a) * h * ln * 0.5, ty + math.sin(a) * h * ln * 0.5 - h * 0.06
        s += (f'<path d="M{tx:.1f} {ty:.1f} Q{mx:.1f} {my-h*0.07:.1f} {ex:.1f} {ey:.1f} Q{mx:.1f} {my+h*0.05:.1f} {tx:.1f} {ty:.1f} Z" '
              f'fill="#2ea84e" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    s += f'<circle cx="{tx:.1f}" cy="{ty+6:.1f}" r="{h*0.035:.1f}" fill="#7a4b28" stroke="{INK}" stroke-width="3"/>'
    return s


def pagoda(X, y, h, tiers=4):
    s = ""
    th = h / (tiers + 0.6)
    for i in range(tiers):
        bw = h * 0.36 * (1 - i * 0.16)
        yb = y - i * th
        s += f'<rect x="{X-bw/2:.1f}" y="{yb-th*0.75:.1f}" width="{bw:.1f}" height="{th*0.75:.1f}" fill="#f4ead2" stroke="{INK}" stroke-width="4"/>'
        s += f'<rect x="{X-bw*0.12:.1f}" y="{yb-th*0.55:.1f}" width="{bw*0.24:.1f}" height="{th*0.4:.1f}" fill="#c0392b" stroke="{INK}" stroke-width="2"/>'
        rw = bw * 1.55
        ry = yb - th * 0.72
        s += (f'<path d="M{X-rw/2:.1f} {ry:.1f} Q{X-rw*0.3:.1f} {ry-th*0.12:.1f} {X-bw*0.35:.1f} {ry-th*0.32:.1f} L{X+bw*0.35:.1f} {ry-th*0.32:.1f} '
              f'Q{X+rw*0.3:.1f} {ry-th*0.12:.1f} {X+rw/2:.1f} {ry:.1f} Q{X:.1f} {ry-th*0.08:.1f} {X-rw/2:.1f} {ry:.1f} Z" '
              f'fill="#d9534f" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    ty = y - tiers * th - th * 0.05
    s += f'<line x1="{X:.1f}" y1="{ty:.1f}" x2="{X:.1f}" y2="{ty-th*0.7:.1f}" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
    for k in range(3):
        s += f'<circle cx="{X:.1f}" cy="{ty-th*(0.18+0.18*k):.1f}" r="5" fill="#f5b82e" stroke="{INK}" stroke-width="2"/>'
    return s


def gate(X, y, w, h):
    pw = w * 0.09
    s = ""
    for px in (X - w * 0.36, X + w * 0.36):
        s += f'<rect x="{px-pw/2:.1f}" y="{y-h:.1f}" width="{pw:.1f}" height="{h:.1f}" fill="#e2483a" stroke="{INK}" stroke-width="5"/>'
        s += f'<rect x="{px-pw*0.7:.1f}" y="{y-14:.1f}" width="{pw*1.4:.1f}" height="14" fill="#2b2b2b" stroke="{INK}" stroke-width="4"/>'
    s += f'<rect x="{X-w*0.45:.1f}" y="{y-h*0.78:.1f}" width="{w*0.9:.1f}" height="{h*0.07:.1f}" fill="#e2483a" stroke="{INK}" stroke-width="5"/>'
    s += f'<rect x="{X-w*0.06:.1f}" y="{y-h*0.92:.1f}" width="{w*0.12:.1f}" height="{h*0.16:.1f}" fill="#e2483a" stroke="{INK}" stroke-width="4"/>'
    s += (f'<path d="M{X-w*0.56:.1f} {y-h*1.04:.1f} Q{X:.1f} {y-h*0.9:.1f} {X+w*0.56:.1f} {y-h*1.04:.1f} L{X+w*0.5:.1f} {y-h*0.92:.1f} '
          f'Q{X:.1f} {y-h*0.84:.1f} {X-w*0.5:.1f} {y-h*0.92:.1f} Z" fill="#2b2b2b" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
          f'<path d="M{X-w*0.5:.1f} {y-h*0.92:.1f} Q{X:.1f} {y-h*0.84:.1f} {X+w*0.5:.1f} {y-h*0.92:.1f} L{X+w*0.48:.1f} {y-h*0.86:.1f} '
          f'Q{X:.1f} {y-h*0.79:.1f} {X-w*0.48:.1f} {y-h*0.86:.1f} Z" fill="#e2483a" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    return s


def lantern(X, y, h):
    g = "#b9bdb5"
    return (f'<rect x="{X-h*0.18:.1f}" y="{y-h*0.1:.1f}" width="{h*0.36:.1f}" height="{h*0.1:.1f}" fill="{g}" stroke="{INK}" stroke-width="4"/>'
            f'<rect x="{X-h*0.07:.1f}" y="{y-h*0.5:.1f}" width="{h*0.14:.1f}" height="{h*0.4:.1f}" fill="{g}" stroke="{INK}" stroke-width="4"/>'
            f'<rect x="{X-h*0.16:.1f}" y="{y-h*0.74:.1f}" width="{h*0.32:.1f}" height="{h*0.24:.1f}" fill="{g}" stroke="{INK}" stroke-width="4"/>'
            f'<rect x="{X-h*0.08:.1f}" y="{y-h*0.7:.1f}" width="{h*0.16:.1f}" height="{h*0.16:.1f}" fill="#ffd36b"/>'
            f'<path d="M{X-h*0.28:.1f} {y-h*0.74:.1f} L{X:.1f} {y-h*0.95:.1f} L{X+h*0.28:.1f} {y-h*0.74:.1f} Z" fill="{g}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<circle cx="{X:.1f}" cy="{y-h*0.98:.1f}" r="{h*0.04:.1f}" fill="{g}" stroke="{INK}" stroke-width="3"/>')


def standing_stone(X, y, w, h, c="#a7b0bd"):
    return (f'<path d="M{X-w/2:.1f} {y:.1f} L{X-w*0.45:.1f} {y-h+w*0.3:.1f} Q{X-w*0.3:.1f} {y-h:.1f} {X:.1f} {y-h:.1f} '
            f'Q{X+w*0.35:.1f} {y-h:.1f} {X+w*0.45:.1f} {y-h+w*0.35:.1f} L{X+w/2:.1f} {y:.1f} Z" fill="{c}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M{X-w*0.12:.1f} {y-h*0.6:.1f} L{X:.1f} {y-h*0.72:.1f} L{X+w*0.12:.1f} {y-h*0.6:.1f} M{X:.1f} {y-h*0.72:.1f} L{X:.1f} {y-h*0.45:.1f}" '
            f'fill="none" stroke="#7ef0ff" stroke-width="4" stroke-linecap="round"/>'
            f'<path d="M{X-w*0.3:.1f} {y-h*0.85:.1f} L{X-w*0.3:.1f} {y-h*0.3:.1f}" stroke="#ffffff" stroke-opacity="0.35" stroke-width="5" stroke-linecap="round"/>')


def trilithon(X, y, w, h):
    sw_ = w * 0.28
    s = standing_stone(X - w / 2 + sw_ / 2, y, sw_, h) + standing_stone(X + w / 2 - sw_ / 2, y, sw_, h)
    s += f'<rect x="{X-w/2-8:.1f}" y="{y-h-30:.1f}" width="{w+16:.1f}" height="44" rx="10" fill="#9aa4b2" stroke="{INK}" stroke-width="5"/>'
    return s


def crystals(X, y, s, c="#b98cff", c2="#e2ccff"):
    out = f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{s*1.1:.1f}" ry="{s*0.25:.1f}" fill="{c}" opacity="0.25"/>'
    for dx, hh, ww, tilt in ((-0.55, 0.9, 0.32, -14), (0.5, 1.0, 0.34, 12), (0.0, 1.5, 0.42, 0), (-0.2, 0.7, 0.26, -30)):
        cx = X + dx * s
        hw = ww * s / 2
        top = y - hh * s
        pts = f"{cx-hw:.1f},{y:.1f} {cx-hw:.1f},{top+hw:.1f} {cx:.1f},{top:.1f} {cx+hw:.1f},{top+hw:.1f} {cx+hw:.1f},{y:.1f}"
        out += (f'<g transform="rotate({tilt} {cx:.1f} {y:.1f})"><polygon points="{pts}" fill="{c}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
                f'<polygon points="{cx:.1f},{top:.1f} {cx+hw:.1f},{top+hw:.1f} {cx+hw:.1f},{y:.1f} {cx:.1f},{y:.1f}" fill="{c2}" opacity="0.6"/></g>')
    return out


def mushroom(X, y, s):
    return (f'<rect x="{X-s*0.18:.1f}" y="{y-s*0.6:.1f}" width="{s*0.36:.1f}" height="{s*0.6:.1f}" rx="{s*0.12:.1f}" fill="#f4ead2" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{X-s*0.6:.1f} {y-s*0.55:.1f} Q{X-s*0.6:.1f} {y-s*1.2:.1f} {X:.1f} {y-s*1.2:.1f} Q{X+s*0.6:.1f} {y-s*1.2:.1f} {X+s*0.6:.1f} {y-s*0.55:.1f} Z" '
            f'fill="#ff5a6e" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<circle cx="{X-s*0.25:.1f}" cy="{y-s*0.85:.1f}" r="{s*0.1:.1f}" fill="#fff"/><circle cx="{X+s*0.2:.1f}" cy="{y-s*0.95:.1f}" r="{s*0.08:.1f}" fill="#fff"/>')


def fern(X, y, s):
    out = ""
    for ang in (-150, -120, -95, -70, -40):
        a = math.radians(ang)
        ex, ey = X + math.cos(a) * s, y + math.sin(a) * s
        out += (f'<path d="M{X:.1f} {y:.1f} Q{(X+ex)/2 - math.sin(a)*s*0.25:.1f} {(y+ey)/2 + math.cos(a)*s*0.25:.1f} {ex:.1f} {ey:.1f} '
                f'Q{(X+ex)/2 + math.sin(a)*s*0.15:.1f} {(y+ey)/2 - math.cos(a)*s*0.15:.1f} {X:.1f} {y:.1f} Z" fill="#2a9e4b" stroke="{INK}" stroke-width="3"/>')
    return out


def drum(X, y, s):
    return (f'<rect x="{X-s:.1f}" y="{y-s*0.55:.1f}" width="{s*2:.1f}" height="{s*0.55:.1f}" fill="{STONE}" stroke="{INK}" stroke-width="4"/>'
            f'<ellipse cx="{X+s:.1f}" cy="{y-s*0.275:.1f}" rx="{s*0.14:.1f}" ry="{s*0.275:.1f}" fill="{STONE_D}" stroke="{INK}" stroke-width="4"/>'
            f'<line x1="{X-s*0.6:.1f}" y1="{y-s*0.42:.1f}" x2="{X+s*0.7:.1f}" y2="{y-s*0.42:.1f}" stroke="{STONE_D}" stroke-width="3"/>')


def tile(X, y, s):
    return f'<path d="M{X-s:.1f} {y:.1f} L{X-s*0.7:.1f} {y-s*0.35:.1f} L{X+s*0.8:.1f} {y-s*0.35:.1f} L{X+s:.1f} {y:.1f} Z" fill="{STONE}" stroke="{INK}" stroke-width="3"/>'


def stepping_stone(X, y, s):
    return f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{s:.1f}" ry="{s*0.38:.1f}" fill="#c9cfc4" stroke="{INK}" stroke-width="3"/>'


def petal(X, y, rot):
    return f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="6" ry="3.5" transform="rotate({rot:.0f} {X:.1f} {y:.1f})" fill="#ffb3d1" stroke="{INK}" stroke-width="1.5"/>'


def glow_flower(X, y):
    return (f'<circle cx="{X:.1f}" cy="{y:.1f}" r="13" fill="#7ef0ff" opacity="0.25"/>'
            + flower(X, y, "#7ef0ff"))


# Tiny stroke font (glyph box 10x16, baseline y=16) so sign text renders anywhere, with no font needed.
GLYPHS = {
    "0": "M5 0 C9 0 10 4 10 8 C10 12 9 16 5 16 C1 16 0 12 0 8 C0 4 1 0 5 0 Z",
    "1": "M2 3 L6 0 L6 16 M2 16 L10 16",
    "2": "M0 4 C0 1 3 0 5 0 C8 0 10 2 10 4.5 C10 8 0 12 0 16 L10 16",
    "3": "M0 2 C2 0 9 -1 9.5 4 C10 7 6 8 4 8 C7 8 10 9 10 12 C10 16 2 17 0 14",
    "4": "M7 16 L7 0 L0 11 L10 11",
    "5": "M9.5 0 L1 0 L0 7 C3 5.5 10 5.5 10 11 C10 16 3 17 0 14",
    "6": "M9 1 C6 -1 0 1 0 9 C0 14 2 16 5 16 C8 16 10 14 10 11 C10 8 8 6 5 6 C2 6 0 8 0 10",
    "7": "M0 0 L10 0 L4 16",
    "8": "M5 0 C8 0 9.5 2 9.5 4 C9.5 6.5 7 7.5 5 8 C2.5 8.5 0 10 0 12.5 C0 15 2.5 16 5 16 C7.5 16 10 15 10 12.5 C10 10 7.5 8.5 5 8 C3 7.5 0.5 6.5 0.5 4 C0.5 2 2 0 5 0 Z",
    "9": "M10 6 C10 9 8 10 5 10 C2 10 0 8 0 5 C0 2 2 0 5 0 C8 0 10 2 10 6 C10 12 8 16 2 15",
    "y": "M0 5 L5 15 M10 5 L3 20",
    "d": "M10 0 L10 16 M10 11 C10 7 8 5 5.5 5 C2 5 0 7 0 10.5 C0 14 2 16 5.5 16 C8 16 10 14 10 11",
}


def stroke_text(cx, cy, text, height):
    sc = height / 16
    adv = {c: (8 if c == " " else 13) for c in text}
    total = sum(adv[c] for c in text) - 3
    x = cx - total * sc / 2
    out = ""
    for c in text:
        if c in GLYPHS:
            out += (f'<path d="{GLYPHS[c]}" transform="translate({x:.1f} {cy - height/2:.1f}) scale({sc:.3f})" fill="none" '
                    f'stroke="{INK}" stroke-width="{2.6:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
        x += adv[c] * sc
    return out


def sign(X, y, text):
    return (f'<rect x="{X-6:.1f}" y="{y-110:.1f}" width="12" height="112" rx="3" fill="#8a5a32" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{X-62:.1f} {y-128:.1f} L{X+52:.1f} {y-128:.1f} L{X+72:.1f} {y-106:.1f} L{X+52:.1f} {y-84:.1f} L{X-62:.1f} {y-84:.1f} Z" '
            f'fill="#c98a4b" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            + stroke_text(X - 2, y - 106, text, 21))


def far_peak(X, y, w, h, c, snow=False):
    s = f'<path d="M{X-w/2:.1f} {y:.1f} L{X-w*0.08:.1f} {y-h:.1f} Q{X:.1f} {y-h*1.04:.1f} {X+w*0.08:.1f} {y-h:.1f} L{X+w/2:.1f} {y:.1f} Z" fill="{c}"/>'
    if snow:
        s += (f'<path d="M{X-w*0.08-w*0.42*0.28:.1f} {y-h*0.72:.1f} L{X-w*0.08:.1f} {y-h:.1f} Q{X:.1f} {y-h*1.04:.1f} {X+w*0.08:.1f} {y-h:.1f} '
              f'L{X+w*0.08+w*0.42*0.28:.1f} {y-h*0.72:.1f} L{X+w*0.06:.1f} {y-h*0.78:.1f} L{X:.1f} {y-h*0.7:.1f} L{X-w*0.07:.1f} {y-h*0.79:.1f} Z" fill="#ffffff"/>')
    return s


def far_mesa(X, y, w, h, c):
    return f'<path d="M{X-w/2:.1f} {y:.1f} L{X-w*0.36:.1f} {y-h:.1f} L{X+w*0.34:.1f} {y-h:.1f} L{X+w/2:.1f} {y:.1f} Z" fill="{c}"/>'


def far_ziggurat(X, y, w, h, c):
    out, n = "", 5
    for i in range(n):
        sw_ = w * (1 - i * 0.17)
        out += f'<rect x="{X-sw_/2:.1f}" y="{y-(i+1)*h/n:.1f}" width="{sw_:.1f}" height="{h/n+1:.1f}" fill="{c}"/>'
    return out


def far_colonnade(X, y, w, h, c):
    out = f'<rect x="{X-w/2:.1f}" y="{y-h:.1f}" width="{w:.1f}" height="{h*0.12:.1f}" fill="{c}"/>'
    out += f'<path d="M{X-w/2:.1f} {y-h:.1f} L{X:.1f} {y-h*1.3:.1f} L{X+w/2:.1f} {y-h:.1f} Z" fill="{c}"/>'
    for i in range(6):
        cx = X - w / 2 + w * (i + 0.5) / 6
        out += f'<rect x="{cx-w*0.03:.1f}" y="{y-h*0.88:.1f}" width="{w*0.06:.1f}" height="{h*0.88:.1f}" fill="{c}"/>'
    return out


def far_pagoda(X, y, h, c):
    out = ""
    for i in range(4):
        bw = h * 0.5 * (1 - i * 0.18)
        yb = y - i * h / 4.4
        out += f'<rect x="{X-bw*0.3:.1f}" y="{yb-h/4.4:.1f}" width="{bw*0.6:.1f}" height="{h/4.4:.1f}" fill="{c}"/>'
        out += f'<path d="M{X-bw/2:.1f} {yb-h/4.4*0.75:.1f} L{X:.1f} {yb-h/4.4*1.2:.1f} L{X+bw/2:.1f} {yb-h/4.4*0.75:.1f} Z" fill="{c}"/>'
    return out



# ----------------------------------------------------------------------- zones 7-12 drawings
def leaf(X, y, rot, c):
    return f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="8" ry="4.5" transform="rotate({rot:.0f} {X:.1f} {y:.1f})" fill="{c}" stroke="{INK}" stroke-width="2"/>'


def pebble_dark(X, y):
    return f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="15" ry="9" fill="#5b6470" stroke="{INK}" stroke-width="3"/>'


def shell(X, y, c):
    return (f'<path d="M{X-12:.1f} {y:.1f} A12 12 0 0 1 {X+12:.1f} {y:.1f} Z" fill="{c}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="M{X:.1f} {y:.1f} L{X:.1f} {y-11:.1f} M{X:.1f} {y:.1f} L{X-8:.1f} {y-8:.1f} M{X:.1f} {y:.1f} L{X+8:.1f} {y-8:.1f}" stroke="{INK}" stroke-width="2"/>')


def bay(X, y, w, h, color="#4cc3f0"):
    s = (f'<path d="M{X-w/2:.1f} {y:.1f} Q{X-w/2:.1f} {y-h:.1f} {X-w*0.3:.1f} {y-h:.1f} L{X+w*0.3:.1f} {y-h:.1f} '
         f'Q{X+w/2:.1f} {y-h:.1f} {X+w/2:.1f} {y:.1f} Z" fill="{color}"/>')
    for i in range(5):
        yy = y - h * 0.8 + i * h * 0.16
        s += f'<path d="M{X-w*0.3+i*60:.1f} {yy:.1f} l60 0" stroke="#ffffff" stroke-width="4" stroke-linecap="round" opacity="0.7"/>'
    for bx, sc in ((X - w * 0.18, 1.0), (X + w * 0.22, 0.7)):
        by = y - h * 0.55
        s += (f'<path d="M{bx-30*sc:.1f} {by:.1f} L{bx+30*sc:.1f} {by:.1f} L{bx+20*sc:.1f} {by+12*sc:.1f} L{bx-20*sc:.1f} {by+12*sc:.1f} Z" fill="#ffffff" stroke="{INK}" stroke-width="3"/>'
              f'<path d="M{bx:.1f} {by-2:.1f} L{bx:.1f} {by-50*sc:.1f} L{bx+26*sc:.1f} {by-6:.1f} Z" fill="#ff6b6b" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
    return s


def lighthouse(X, y, h):
    w0, w1 = h * 0.26, h * 0.16
    s = (f'<path d="M{X-w0/2:.1f} {y:.1f} L{X-w1/2:.1f} {y-h*0.78:.1f} L{X+w1/2:.1f} {y-h*0.78:.1f} L{X+w0/2:.1f} {y:.1f} Z" fill="#ffffff" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    for i in range(3):
        t0, t1 = 0.12 + i * 0.24, 0.24 + i * 0.24
        a0, a1 = w0 + (w1 - w0) * t0, w0 + (w1 - w0) * t1
        s += f'<path d="M{X-a0/2:.1f} {y-h*0.78*t0:.1f} L{X-a1/2:.1f} {y-h*0.78*t1:.1f} L{X+a1/2:.1f} {y-h*0.78*t1:.1f} L{X+a0/2:.1f} {y-h*0.78*t0:.1f} Z" fill="#e2483a"/>'
    s += (f'<path d="M{X-w0/2:.1f} {y:.1f} L{X-w1/2:.1f} {y-h*0.78:.1f} L{X+w1/2:.1f} {y-h*0.78:.1f} L{X+w0/2:.1f} {y:.1f} Z" fill="none" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
          f'<rect x="{X-w1*0.75:.1f}" y="{y-h*0.8:.1f}" width="{w1*1.5:.1f}" height="{h*0.04:.1f}" fill="#2b2b2b" stroke="{INK}" stroke-width="3"/>'
          f'<rect x="{X-w1*0.4:.1f}" y="{y-h*0.92:.1f}" width="{w1*0.8:.1f}" height="{h*0.12:.1f}" fill="#ffe680" stroke="{INK}" stroke-width="4"/>'
          f'<path d="M{X-w1*0.6:.1f} {y-h*0.92:.1f} L{X:.1f} {y-h:.1f} L{X+w1*0.6:.1f} {y-h*0.92:.1f} Z" fill="#e2483a" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    return s


def umbrella(X, y, s_, c1, c2):
    top = y - s_ * 1.4
    dome = f"M{X-s_:.1f} {top+s_*0.35:.1f} Q{X-s_:.1f} {top-s_*0.45:.1f} {X:.1f} {top-s_*0.45:.1f} Q{X+s_:.1f} {top-s_*0.45:.1f} {X+s_:.1f} {top+s_*0.35:.1f} Z"
    cid = f"u{int(X)}"
    out = (f'<line x1="{X:.1f}" y1="{y:.1f}" x2="{X:.1f}" y2="{top:.1f}" stroke="{INK}" stroke-width="7"/>'
           f'<line x1="{X:.1f}" y1="{y:.1f}" x2="{X:.1f}" y2="{top:.1f}" stroke="#f4f4f4" stroke-width="3"/>'
           f'<clipPath id="{cid}"><path d="{dome}"/></clipPath><path d="{dome}" fill="{c1}"/><g clip-path="url(#{cid})">')
    for i in range(-2, 3, 2):
        out += f'<rect x="{X + i*s_*0.4 - s_*0.2:.1f}" y="{top-s_:.1f}" width="{s_*0.4:.1f}" height="{s_*2:.1f}" fill="{c2}"/>'
    return out + f'</g><path d="{dome}" fill="none" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'


def windmill(X, y, h, rot=18):
    s = (f'<path d="M{X-h*0.16:.1f} {y:.1f} L{X-h*0.1:.1f} {y-h*0.72:.1f} L{X+h*0.1:.1f} {y-h*0.72:.1f} L{X+h*0.16:.1f} {y:.1f} Z" fill="#f4ead2" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
         f'<rect x="{X-h*0.04:.1f}" y="{y-h*0.16:.1f}" width="{h*0.08:.1f}" height="{h*0.16:.1f}" rx="{h*0.04:.1f}" fill="#8a5a32" stroke="{INK}" stroke-width="4"/>'
         f'<rect x="{X-h*0.03:.1f}" y="{y-h*0.48:.1f}" width="{h*0.06:.1f}" height="{h*0.07:.1f}" fill="#7ad0ff" stroke="{INK}" stroke-width="3"/>'
         f'<path d="M{X-h*0.14:.1f} {y-h*0.7:.1f} Q{X:.1f} {y-h*0.86:.1f} {X+h*0.14:.1f} {y-h*0.7:.1f} Z" fill="#c0392b" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    cx, cy = X, y - h * 0.74
    for k in range(4):
        a = rot + 90 * k
        s += (f'<g transform="rotate({a} {cx:.1f} {cy:.1f})"><rect x="{cx-h*0.025:.1f}" y="{cy-h*0.5:.1f}" width="{h*0.05:.1f}" height="{h*0.5:.1f}" fill="#8a5a32" stroke="{INK}" stroke-width="3"/>'
              f'<rect x="{cx+h*0.025:.1f}" y="{cy-h*0.48:.1f}" width="{h*0.1:.1f}" height="{h*0.36:.1f}" fill="#ffffff" stroke="{INK}" stroke-width="4"/></g>')
    s += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{h*0.035:.1f}" fill="#f5b82e" stroke="{INK}" stroke-width="3"/>'
    return s


def barn(X, y, w, h):
    return (f'<path d="M{X-w/2:.1f} {y:.1f} L{X-w/2:.1f} {y-h*0.55:.1f} L{X-w*0.32:.1f} {y-h*0.85:.1f} L{X:.1f} {y-h:.1f} L{X+w*0.32:.1f} {y-h*0.85:.1f} '
            f'L{X+w/2:.1f} {y-h*0.55:.1f} L{X+w/2:.1f} {y:.1f} Z" fill="#d94b3d" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<path d="M{X-w/2-8:.1f} {y-h*0.53:.1f} L{X-w*0.33:.1f} {y-h*0.87:.1f} L{X:.1f} {y-h-6:.1f} L{X+w*0.33:.1f} {y-h*0.87:.1f} L{X+w/2+8:.1f} {y-h*0.53:.1f}" fill="none" stroke="#f4f4f4" stroke-width="10" stroke-linejoin="round"/>'
            f'<rect x="{X-w*0.18:.1f}" y="{y-h*0.42:.1f}" width="{w*0.36:.1f}" height="{h*0.42:.1f}" fill="#b83a2f" stroke="#f4f4f4" stroke-width="6"/>'
            f'<path d="M{X-w*0.18:.1f} {y-h*0.42:.1f} L{X+w*0.18:.1f} {y:.1f} M{X+w*0.18:.1f} {y-h*0.42:.1f} L{X-w*0.18:.1f} {y:.1f}" stroke="#f4f4f4" stroke-width="5"/>'
            f'<rect x="{X-w*0.08:.1f}" y="{y-h*0.75:.1f}" width="{w*0.16:.1f}" height="{h*0.14:.1f}" fill="#ffe680" stroke="{INK}" stroke-width="4"/>')


def hay_bale(X, y, r):
    w, h = r * 2.4, r * 1.5
    out = f'<rect x="{X-w/2:.1f}" y="{y-h:.1f}" width="{w:.1f}" height="{h:.1f}" rx="8" fill="#f2c94c" stroke="{INK}" stroke-width="5"/>'
    for i in range(1, 4):
        out += f'<line x1="{X-w/2+6:.1f}" y1="{y-h*i/4:.1f}" x2="{X+w/2-6:.1f}" y2="{y-h*i/4:.1f}" stroke="#d9a92b" stroke-width="3"/>'
    for t in (-0.25, 0.25):
        out += f'<line x1="{X+w*t:.1f}" y1="{y-h:.1f}" x2="{X+w*t:.1f}" y2="{y:.1f}" stroke="#a0522d" stroke-width="5"/>'
    return out


def fence(X, y, w):
    s = ""
    n = int(w / 46)
    x0 = X - w / 2
    for rail in (0.35, 0.7):
        s += f'<rect x="{x0:.1f}" y="{y-56*rail-5:.1f}" width="{w:.1f}" height="10" fill="#f4f4f4" stroke="{INK}" stroke-width="3"/>'
    for i in range(n + 1):
        px = x0 + i * w / n
        s += f'<path d="M{px-7:.1f} {y:.1f} L{px-7:.1f} {y-58:.1f} L{px:.1f} {y-66:.1f} L{px+7:.1f} {y-58:.1f} L{px+7:.1f} {y:.1f} Z" fill="#ffffff" stroke="{INK}" stroke-width="3"/>'
    return s


def pumpkin(X, y, s_):
    return (f'<ellipse cx="{X-s_*0.32:.1f}" cy="{y-s_*0.5:.1f}" rx="{s_*0.42:.1f}" ry="{s_*0.5:.1f}" fill="#f28c28" stroke="{INK}" stroke-width="4"/>'
            f'<ellipse cx="{X+s_*0.32:.1f}" cy="{y-s_*0.5:.1f}" rx="{s_*0.42:.1f}" ry="{s_*0.5:.1f}" fill="#f28c28" stroke="{INK}" stroke-width="4"/>'
            f'<ellipse cx="{X:.1f}" cy="{y-s_*0.5:.1f}" rx="{s_*0.4:.1f}" ry="{s_*0.52:.1f}" fill="#ff9f43" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{X:.1f} {y-s_:.1f} Q{X+s_*0.05:.1f} {y-s_*1.25:.1f} {X+s_*0.2:.1f} {y-s_*1.3:.1f}" fill="none" stroke="#3a7a3a" stroke-width="7" stroke-linecap="round"/>')


def volcano(X, y, w, h):
    s = (f'<path d="M{X-w/2:.1f} {y:.1f} L{X-w*0.12:.1f} {y-h:.1f} L{X+w*0.12:.1f} {y-h:.1f} L{X+w/2:.1f} {y:.1f} Z" fill="#7d8a86"/>'
         f'<path d="M{X-w*0.12:.1f} {y-h:.1f} L{X-w*0.16:.1f} {y-h*0.75:.1f} L{X-w*0.08:.1f} {y-h*0.82:.1f} L{X-w*0.04:.1f} {y-h*0.6:.1f} L{X+w*0.02:.1f} {y-h*0.8:.1f} '
         f'L{X+w*0.08:.1f} {y-h*0.68:.1f} L{X+w*0.12:.1f} {y-h*0.85:.1f} L{X+w*0.12:.1f} {y-h:.1f} Z" fill="#ff8a3d"/>'
         f'<path d="M{X-w*0.1:.1f} {y-h:.1f} L{X+w*0.1:.1f} {y-h:.1f}" stroke="#ffd34d" stroke-width="10" stroke-linecap="round"/>')
    for i, (dx, dy, r) in enumerate(((0, -60, 46), (40, -130, 58), (-20, -210, 70), (60, -290, 82))):
        s += f'<circle cx="{X+dx:.1f}" cy="{y-h+dy:.1f}" r="{r}" fill="#b9bdb5" opacity="{0.75 - i*0.12:.2f}"/>'
    return s


def burnt_tree(X, y, h):
    return (f'<path d="M{X:.1f} {y:.1f} L{X:.1f} {y-h:.1f} M{X:.1f} {y-h*0.55:.1f} L{X-h*0.25:.1f} {y-h*0.8:.1f} M{X:.1f} {y-h*0.7:.1f} L{X+h*0.22:.1f} {y-h*0.92:.1f} '
            f'M{X:.1f} {y-h*0.35:.1f} L{X+h*0.18:.1f} {y-h*0.5:.1f}" fill="none" stroke="{INK}" stroke-width="{h*0.09+6:.1f}" stroke-linecap="round"/>'
            f'<path d="M{X:.1f} {y:.1f} L{X:.1f} {y-h:.1f} M{X:.1f} {y-h*0.55:.1f} L{X-h*0.25:.1f} {y-h*0.8:.1f} M{X:.1f} {y-h*0.7:.1f} L{X+h*0.22:.1f} {y-h*0.92:.1f} '
            f'M{X:.1f} {y-h*0.35:.1f} L{X+h*0.18:.1f} {y-h*0.5:.1f}" fill="none" stroke="#4a3b35" stroke-width="{h*0.09:.1f}" stroke-linecap="round"/>')


def lava_rock(X, y, w, h):
    return (boulder(X, y, w, h, c="#5b6470")
            + f'<path d="M{X-w*0.2:.1f} {y-h*0.6:.1f} L{X:.1f} {y-h*0.4:.1f} L{X+w*0.05:.1f} {y-h*0.15:.1f} M{X:.1f} {y-h*0.4:.1f} L{X+w*0.25:.1f} {y-h*0.55:.1f}" '
              f'fill="none" stroke="#ff8a3d" stroke-width="5" stroke-linecap="round"/>')


def rainbow(X, y, r):
    out = ""
    for i, c in enumerate(("#ff6b6b", "#ffb02e", "#ffe14d", "#6fd66f", "#4cc3f0", "#9b7bff")):
        rr = r - i * 26
        out += f'<path d="M{X-rr:.1f} {y:.1f} A{rr:.1f} {rr:.1f} 0 0 1 {X+rr:.1f} {y:.1f}" fill="none" stroke="{c}" stroke-width="26" opacity="0.55"/>'
    return out


def float_isle(X, y, s_, tree=True):
    out = (f'<path d="M{X-s_:.1f} {y:.1f} Q{X-s_*0.6:.1f} {y+s_*0.55:.1f} {X-s_*0.1:.1f} {y+s_*1.1:.1f} Q{X+s_*0.35:.1f} {y+s_*0.6:.1f} {X+s_:.1f} {y:.1f} Z" '
           f'fill="#a3aca2" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
           f'<path d="M{X-s_*1.05:.1f} {y+2:.1f} Q{X:.1f} {y-s_*0.22:.1f} {X+s_*1.05:.1f} {y+2:.1f} Q{X:.1f} {y+s_*0.14:.1f} {X-s_*1.05:.1f} {y+2:.1f} Z" '
           f'fill="#55c36b" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    if tree:
        out += round_tree(X + s_ * 0.2, y - s_ * 0.05, s_ * 0.9, "#38b8a0")
    return out


def castle(X, y, w, h):
    stone, stone_d = "#d9d4c7", "#b8b1a2"
    s = ""
    # back wall with crenellations
    wall_top = y - h * 0.55
    s += f'<rect x="{X-w*0.38:.1f}" y="{wall_top:.1f}" width="{w*0.76:.1f}" height="{h*0.55:.1f}" fill="{stone}" stroke="{INK}" stroke-width="5"/>'
    for i in range(9):
        cx = X - w * 0.38 + i * w * 0.76 / 8.5
        s += f'<rect x="{cx:.1f}" y="{wall_top-22:.1f}" width="{w*0.045:.1f}" height="24" fill="{stone}" stroke="{INK}" stroke-width="4"/>'
    # keep
    kw, kh = w * 0.3, h * 0.85
    s += f'<rect x="{X-kw/2:.1f}" y="{y-kh:.1f}" width="{kw:.1f}" height="{kh:.1f}" fill="{stone}" stroke="{INK}" stroke-width="5"/>'
    s += f'<path d="M{X-kw*0.62:.1f} {y-kh:.1f} L{X:.1f} {y-h*1.12:.1f} L{X+kw*0.62:.1f} {y-kh:.1f} Z" fill="#4a7bd9" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
    s += f'<line x1="{X:.1f}" y1="{y-h*1.12:.1f}" x2="{X:.1f}" y2="{y-h*1.26:.1f}" stroke="{INK}" stroke-width="4"/>'
    s += f'<path d="M{X:.1f} {y-h*1.26:.1f} L{X+40:.1f} {y-h*1.22:.1f} L{X:.1f} {y-h*1.17:.1f} Z" fill="#ffd34d" stroke="{INK}" stroke-width="3"/>'
    for wx in (-0.07, 0.07):
        s += f'<rect x="{X+w*wx-10:.1f}" y="{y-kh*0.75:.1f}" width="20" height="34" rx="10" fill="#2a2333"/>'
    # towers
    for tx, th in ((-0.42, 0.75), (0.42, 0.75)):
        cx = X + w * tx
        tw_ = w * 0.13
        s += f'<rect x="{cx-tw_/2:.1f}" y="{y-h*th:.1f}" width="{tw_:.1f}" height="{h*th:.1f}" fill="{stone_d}" stroke="{INK}" stroke-width="5"/>'
        s += f'<path d="M{cx-tw_*0.7:.1f} {y-h*th:.1f} L{cx:.1f} {y-h*th-h*0.28:.1f} L{cx+tw_*0.7:.1f} {y-h*th:.1f} Z" fill="#e2483a" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
        s += f'<rect x="{cx-8:.1f}" y="{y-h*th*0.7:.1f}" width="16" height="28" rx="8" fill="#2a2333"/>'
    # gate
    s += (f'<path d="M{X-w*0.07:.1f} {y:.1f} L{X-w*0.07:.1f} {y-h*0.2:.1f} A{w*0.07:.1f} {w*0.07:.1f} 0 0 1 {X+w*0.07:.1f} {y-h*0.2:.1f} L{X+w*0.07:.1f} {y:.1f} Z" '
          f'fill="#7a4b28" stroke="{INK}" stroke-width="5"/>')
    for gx in (-0.035, 0.0, 0.035):
        s += f'<line x1="{X+w*gx:.1f}" y1="{y:.1f}" x2="{X+w*gx:.1f}" y2="{y-h*0.24:.1f}" stroke="{INK}" stroke-width="3"/>'
    # banners
    for bx, c in ((-0.25, "#e2483a"), (0.25, "#4a7bd9")):
        cx = X + w * bx
        s += f'<path d="M{cx-18:.1f} {wall_top+20:.1f} L{cx+18:.1f} {wall_top+20:.1f} L{cx+18:.1f} {wall_top+110:.1f} L{cx:.1f} {wall_top+92:.1f} L{cx-18:.1f} {wall_top+110:.1f} Z" fill="{c}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
        s += f'<circle cx="{cx:.1f}" cy="{wall_top+52:.1f}" r="9" fill="#ffd34d" stroke="{INK}" stroke-width="3"/>'
    return s


def pennant_line(X, y, w):
    s = f'<path d="M{X-w/2:.1f} {y:.1f} Q{X:.1f} {y+40:.1f} {X+w/2:.1f} {y:.1f}" fill="none" stroke="{INK}" stroke-width="3"/>'
    cols = ["#e2483a", "#ffd34d", "#4a7bd9", "#3fb45a"]
    for i in range(9):
        t = (i + 0.5) / 9
        px = X - w / 2 + w * t
        py = y + 40 * 4 * t * (1 - t) * 0.5 * 2 / 2
        s += f'<path d="M{px-12:.1f} {py:.1f} L{px+12:.1f} {py:.1f} L{px:.1f} {py+28:.1f} Z" fill="{cols[i % 4]}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
    return s


def banner_pole(X, y, h, c):
    return (f'<rect x="{X-5:.1f}" y="{y-h:.1f}" width="10" height="{h:.1f}" rx="5" fill="#f4f4f4" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{X+5:.1f} {y-h+6:.1f} Q{X+50:.1f} {y-h:.1f} {X+90:.1f} {y-h+20:.1f} Q{X+50:.1f} {y-h+34:.1f} {X+5:.1f} {y-h+46:.1f} Z" fill="{c}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<circle cx="{X:.1f}" cy="{y-h:.1f}" r="8" fill="#ffd34d" stroke="{INK}" stroke-width="3"/>')


# ----------------------------------------------------------------------- zones 13-17 drawings
def moon(X, y, r):
    return (f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r*2.2:.1f}" fill="#fff7c2" opacity="0.12"/>'
            f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#fff3c4" stroke="#f5d97a" stroke-width="6"/>'
            f'<circle cx="{X-r*0.3:.1f}" cy="{y-r*0.2:.1f}" r="{r*0.18:.1f}" fill="#f0dfa0"/>'
            f'<circle cx="{X+r*0.35:.1f}" cy="{y+r*0.25:.1f}" r="{r*0.12:.1f}" fill="#f0dfa0"/>')


def snow_pine(X, y, h):
    s = pine_tree(X, y, h, "#2f7d5b", "#3a8f69")
    for wf, top, bot in ((0.42, 0.55, 0.12), (0.34, 0.80, 0.38), (0.24, 1.0, 0.62)):
        s += (f'<path d="M{X-h*wf*0.45:.1f} {y-h*(top-(top-bot)*0.45):.1f} L{X:.1f} {y-h*top:.1f} L{X+h*wf*0.45:.1f} {y-h*(top-(top-bot)*0.45):.1f} '
              f'Q{X:.1f} {y-h*(top-(top-bot)*0.3):.1f} {X-h*wf*0.45:.1f} {y-h*(top-(top-bot)*0.45):.1f} Z" fill="#ffffff"/>')
    return s


def snowman(X, y, s_):
    return (blob([(X, y - s_ * 0.45, s_ * 0.45)], "#ffffff", sw=3) + blob([(X, y - s_ * 1.15, s_ * 0.32)], "#ffffff", sw=3)
            + blob([(X, y - s_ * 1.65, s_ * 0.22)], "#ffffff", sw=3)
            + f'<circle cx="{X-s_*0.07:.1f}" cy="{y-s_*1.7:.1f}" r="{s_*0.03:.1f}" fill="{INK}"/><circle cx="{X+s_*0.07:.1f}" cy="{y-s_*1.7:.1f}" r="{s_*0.03:.1f}" fill="{INK}"/>'
            f'<path d="M{X:.1f} {y-s_*1.64:.1f} L{X+s_*0.22:.1f} {y-s_*1.6:.1f} L{X:.1f} {y-s_*1.58:.1f} Z" fill="#ff8a3d"/>'
            f'<rect x="{X-s_*0.2:.1f}" y="{y-s_*1.92:.1f}" width="{s_*0.4:.1f}" height="{s_*0.08:.1f}" fill="#2b2b2b"/>'
            f'<rect x="{X-s_*0.13:.1f}" y="{y-s_*2.1:.1f}" width="{s_*0.26:.1f}" height="{s_*0.2:.1f}" fill="#2b2b2b"/>'
            f'<path d="M{X-s_*0.28:.1f} {y-s_*1.42:.1f} Q{X:.1f} {y-s_*1.32:.1f} {X+s_*0.3:.1f} {y-s_*1.44:.1f}" stroke="#e2483a" stroke-width="{s_*0.08:.1f}" fill="none" stroke-linecap="round"/>'
            f'<path d="M{X-s_*0.3:.1f} {y-s_*1.15:.1f} L{X-s_*0.7:.1f} {y-s_*1.45:.1f} M{X+s_*0.3:.1f} {y-s_*1.15:.1f} L{X+s_*0.7:.1f} {y-s_*1.4:.1f}" stroke="#7a4b28" stroke-width="5" stroke-linecap="round"/>')


def igloo(X, y, w):
    h = w * 0.55
    s = f'<path d="M{X-w/2:.1f} {y:.1f} A{w/2:.1f} {h:.1f} 0 0 1 {X+w/2:.1f} {y:.1f} Z" fill="#f4f9fc" stroke="{INK}" stroke-width="5"/>'
    for i in range(1, 4):
        yy = y - h * i / 4
        hw = (w / 2) * math.sqrt(max(0.0, 1 - (i / 4) ** 2))
        s += f'<line x1="{X-hw:.1f}" y1="{yy:.1f}" x2="{X+hw:.1f}" y2="{yy:.1f}" stroke="#c9dce8" stroke-width="3"/>'
    s += f'<path d="M{X+w*0.12:.1f} {y:.1f} L{X+w*0.12:.1f} {y-h*0.32:.1f} A{w*0.13:.1f} {w*0.13:.1f} 0 0 1 {X+w*0.38:.1f} {y-h*0.32:.1f} L{X+w*0.38:.1f} {y:.1f} Z" fill="#5a7a92" stroke="{INK}" stroke-width="4"/>'
    return s


def snow_lump(X, y):
    return f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="16" ry="8" fill="#ffffff" stroke="#b9cfdc" stroke-width="3"/>'


def cactus(X, y, h):
    w = h * 0.2
    arm = (f'<path d="M{X:.1f} {y-h*0.45:.1f} L{X-h*0.28:.1f} {y-h*0.45:.1f} L{X-h*0.28:.1f} {y-h*0.72:.1f}" fill="none" stroke="{INK}" stroke-width="{w*0.75+8:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
           f'<path d="M{X:.1f} {y-h*0.58:.1f} L{X+h*0.26:.1f} {y-h*0.58:.1f} L{X+h*0.26:.1f} {y-h*0.86:.1f}" fill="none" stroke="{INK}" stroke-width="{w*0.75+8:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    arm_f = arm.replace(f'stroke="{INK}" stroke-width="{w*0.75+8:.1f}"', f'stroke="#4caf62" stroke-width="{w*0.75:.1f}"')
    return (arm + f'<line x1="{X:.1f}" y1="{y:.1f}" x2="{X:.1f}" y2="{y-h:.1f}" stroke="{INK}" stroke-width="{w+8:.1f}" stroke-linecap="round"/>' + arm_f
            + f'<line x1="{X:.1f}" y1="{y:.1f}" x2="{X:.1f}" y2="{y-h:.1f}" stroke="#4caf62" stroke-width="{w:.1f}" stroke-linecap="round"/>'
            f'<line x1="{X-w*0.15:.1f}" y1="{y-h*0.1:.1f}" x2="{X-w*0.15:.1f}" y2="{y-h*0.92:.1f}" stroke="#3a9150" stroke-width="3"/>'
            f'<circle cx="{X:.1f}" cy="{y-h-w*0.2:.1f}" r="{w*0.28:.1f}" fill="#ff8fc7" stroke="{INK}" stroke-width="3"/>')


def oasis(X, y, w):
    return (f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{w/2:.1f}" ry="{w*0.09:.1f}" fill="#4cc3f0" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{X-w*0.25:.1f} {y-2:.1f} l{w*0.15:.1f} 0 M{X+w*0.05:.1f} {y+4:.1f} l{w*0.18:.1f} 0" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>')


def pyramid(X, y, w, h, c):
    return (f'<path d="M{X-w/2:.1f} {y:.1f} L{X:.1f} {y-h:.1f} L{X+w/2:.1f} {y:.1f} Z" fill="{c}"/>'
            f'<path d="M{X:.1f} {y-h:.1f} L{X+w/2:.1f} {y:.1f} L{X+w*0.12:.1f} {y:.1f} Z" fill="#000000" opacity="0.08"/>')


def giant_mushroom(X, y, h, cap, dots="#ffffff"):
    return (f'<path d="M{X-h*0.08:.1f} {y:.1f} Q{X-h*0.1:.1f} {y-h*0.5:.1f} {X-h*0.06:.1f} {y-h*0.72:.1f} L{X+h*0.06:.1f} {y-h*0.72:.1f} Q{X+h*0.1:.1f} {y-h*0.5:.1f} {X+h*0.08:.1f} {y:.1f} Z" fill="#f4ead2" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{X-h*0.42:.1f} {y-h*0.68:.1f} Q{X-h*0.44:.1f} {y-h*1.05:.1f} {X:.1f} {y-h*1.06:.1f} Q{X+h*0.44:.1f} {y-h*1.05:.1f} {X+h*0.42:.1f} {y-h*0.68:.1f} Q{X:.1f} {y-h*0.6:.1f} {X-h*0.42:.1f} {y-h*0.68:.1f} Z" fill="{cap}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            + "".join(f'<circle cx="{X+dx*h:.1f}" cy="{y-dy*h:.1f}" r="{r*h:.1f}" fill="{dots}"/>' for dx, dy, r in ((-0.2, 0.86, 0.05), (0.08, 0.96, 0.06), (0.25, 0.8, 0.04)))
            + f'<path d="M{X-h*0.3:.1f} {y-h*0.88:.1f} Q{X-h*0.2:.1f} {y-h*0.98:.1f} {X-h*0.05:.1f} {y-h*1.0:.1f}" fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round" opacity="0.45"/>')


def spore(X, y, c):
    return f'<circle cx="{X:.1f}" cy="{y:.1f}" r="9" fill="{c}" opacity="0.25"/><circle cx="{X:.1f}" cy="{y:.1f}" r="4" fill="{c}"/>'


def lollipop(X, y, h, c1, c2):
    r = h * 0.28
    return (f'<rect x="{X-4:.1f}" y="{y-h+r:.1f}" width="8" height="{h-r:.1f}" fill="#ffffff" stroke="{INK}" stroke-width="3"/>'
            f'<circle cx="{X:.1f}" cy="{y-h+r*0.3:.1f}" r="{r:.1f}" fill="{c1}" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{X:.1f} {y-h+r*0.3:.1f} m-{r*0.7:.1f} 0 a{r*0.7:.1f} {r*0.7:.1f} 0 1 1 {r*0.7:.1f} {r*0.7:.1f} a{r*0.45:.1f} {r*0.45:.1f} 0 1 1 -{r*0.4:.1f} -{r*0.5:.1f} a{r*0.2:.1f} {r*0.2:.1f} 0 1 1 {r*0.2:.1f} {r*0.25:.1f}" fill="none" stroke="{c2}" stroke-width="{r*0.16:.1f}" stroke-linecap="round"/>')


def candy_cane(X, y, h):
    d = f"M{X:.1f} {y:.1f} L{X:.1f} {y-h*0.75:.1f} A{h*0.15:.1f} {h*0.15:.1f} 0 0 1 {X+h*0.3:.1f} {y-h*0.75:.1f}"
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="{h*0.1+8:.1f}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="{h*0.1:.1f}" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="#e2483a" stroke-width="{h*0.1:.1f}" stroke-linecap="butt" stroke-dasharray="{h*0.06:.1f} {h*0.06:.1f}"/>')


def cupcake(X, y, s_):
    return (f'<path d="M{X-s_*0.45:.1f} {y-s_*0.55:.1f} L{X+s_*0.45:.1f} {y-s_*0.55:.1f} L{X+s_*0.35:.1f} {y:.1f} L{X-s_*0.35:.1f} {y:.1f} Z" fill="#ffb02e" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            + blob([(X - s_ * 0.25, y - s_ * 0.65, s_ * 0.25), (X + s_ * 0.25, y - s_ * 0.65, s_ * 0.25), (X, y - s_ * 0.85, s_ * 0.3)], "#ffc4e2", sw=3)
            + f'<circle cx="{X:.1f}" cy="{y-s_*1.2:.1f}" r="{s_*0.1:.1f}" fill="#e2483a" stroke="{INK}" stroke-width="3"/>')


def gumdrop(X, y, s_, c):
    return (f'<path d="M{X-s_:.1f} {y:.1f} Q{X-s_:.1f} {y-s_*1.4:.1f} {X:.1f} {y-s_*1.4:.1f} Q{X+s_:.1f} {y-s_*1.4:.1f} {X+s_:.1f} {y:.1f} Z" fill="{c}" stroke="{INK}" stroke-width="4"/>'
            f'<circle cx="{X-s_*0.35:.1f}" cy="{y-s_*0.9:.1f}" r="{s_*0.15:.1f}" fill="#ffffff" opacity="0.6"/>')


def sprinkle(X, y, rot, c):
    return f'<rect x="{X-6:.1f}" y="{y-2:.1f}" width="12" height="4" rx="2" transform="rotate({rot:.0f} {X:.1f} {y:.1f})" fill="{c}"/>'


def observatory(X, y, w):
    return (f'<rect x="{X-w*0.4:.1f}" y="{y-w*0.45:.1f}" width="{w*0.8:.1f}" height="{w*0.45:.1f}" fill="#d9d4e8" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{X-w*0.45:.1f} {y-w*0.45:.1f} A{w*0.45:.1f} {w*0.42:.1f} 0 0 1 {X+w*0.45:.1f} {y-w*0.45:.1f} Z" fill="#b9b3d9" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{X+w*0.02:.1f} {y-w*0.85:.1f} L{X+w*0.35:.1f} {y-w*1.1:.1f} L{X+w*0.42:.1f} {y-w*1.0:.1f} L{X+w*0.12:.1f} {y-w*0.72:.1f} Z" fill="#8f89c0" stroke="{INK}" stroke-width="4"/>'
            f'<rect x="{X-w*0.08:.1f}" y="{y-w*0.28:.1f}" width="{w*0.16:.1f}" height="{w*0.28:.1f}" rx="6" fill="#ffd36b" stroke="{INK}" stroke-width="3"/>')


def glow_lamp(X, y, h):
    return (f'<circle cx="{X:.1f}" cy="{y-h:.1f}" r="{h*0.35:.1f}" fill="#ffd36b" opacity="0.25"/>'
            f'<rect x="{X-3:.1f}" y="{y-h:.1f}" width="6" height="{h:.1f}" fill="#2b2b3b" stroke="{INK}" stroke-width="2"/>'
            f'<circle cx="{X:.1f}" cy="{y-h:.1f}" r="{h*0.1:.1f}" fill="#fff1a8" stroke="{INK}" stroke-width="3"/>')


def firefly(X, y):
    return f'<circle cx="{X:.1f}" cy="{y:.1f}" r="10" fill="#fff38a" opacity="0.25"/><circle cx="{X:.1f}" cy="{y:.1f}" r="3.5" fill="#fff38a"/>'


# ----------------------------------------------------------------------- zones 18-22 drawings
def coral(X, y, s_, c):
    out = ""
    for ang, ln in ((-150, 0.9), (-115, 1.2), (-90, 1.0), (-62, 1.15), (-30, 0.85)):
        a = math.radians(ang)
        ex, ey = X + math.cos(a) * s_ * ln, y + math.sin(a) * s_ * ln
        mx, my = X + math.cos(a) * s_ * ln * 0.55, y + math.sin(a) * s_ * ln * 0.55
        for col, wd in ((INK, s_ * 0.2 + 7), (c, s_ * 0.2)):
            out += f'<path d="M{X:.1f} {y:.1f} Q{mx + 8:.1f} {my:.1f} {ex:.1f} {ey:.1f}" fill="none" stroke="{col}" stroke-width="{wd:.1f}" stroke-linecap="round"/>'
        out += blob([(ex, ey, s_ * 0.13)], c, sw=3)
    return out


def seaweed(X, y, h):
    d = f"M{X:.1f} {y:.1f} Q{X-18:.1f} {y-h*0.3:.1f} {X:.1f} {y-h*0.55:.1f} Q{X+18:.1f} {y-h*0.8:.1f} {X+4:.1f} {y-h:.1f}"
    return (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="16" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="#2fa86a" stroke-width="9" stroke-linecap="round"/>')


def starfish(X, y, s_, c):
    pts = []
    for i in range(10):
        r = s_ if i % 2 == 0 else s_ * 0.42
        a = math.radians(-90 + 36 * i)
        pts.append(f"{X + r*math.cos(a):.1f},{y + r*math.sin(a)*0.7:.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{c}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'


def stilt_hut(X, y, w):
    h = w * 0.6
    s = "".join(f'<rect x="{X + dx*w - 4:.1f}" y="{y - h*0.55:.1f}" width="8" height="{h*0.55:.1f}" fill="#8a5a32" stroke="{INK}" stroke-width="3"/>' for dx in (-0.4, -0.1, 0.2, 0.4))
    s += f'<rect x="{X-w/2:.1f}" y="{y-h*0.62:.1f}" width="{w:.1f}" height="12" fill="#a8743f" stroke="{INK}" stroke-width="4"/>'
    s += f'<rect x="{X-w*0.36:.1f}" y="{y-h*1.05:.1f}" width="{w*0.72:.1f}" height="{h*0.43:.1f}" fill="#f2d39b" stroke="{INK}" stroke-width="4"/>'
    s += f'<rect x="{X-w*0.08:.1f}" y="{y-h*0.92:.1f}" width="{w*0.16:.1f}" height="{h*0.3:.1f}" fill="#7a4b28"/>'
    s += f'<path d="M{X-w*0.5:.1f} {y-h*1.02:.1f} L{X:.1f} {y-h*1.4:.1f} L{X+w*0.5:.1f} {y-h*1.02:.1f} Z" fill="#d9b25c" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
    return s


def bamboo(X, y, h, c="#7cc96a"):
    s = f'<rect x="{X-7:.1f}" y="{y-h:.1f}" width="14" height="{h:.1f}" rx="6" fill="{c}" stroke="{INK}" stroke-width="4"/>'
    seg = h / 5
    for i in range(1, 5):
        s += f'<line x1="{X-8:.1f}" y1="{y-i*seg:.1f}" x2="{X+8:.1f}" y2="{y-i*seg:.1f}" stroke="{INK}" stroke-width="3"/>'
        side = 1 if i % 2 else -1
        s += (f'<path d="M{X:.1f} {y-i*seg:.1f} Q{X+side*30:.1f} {y-i*seg-22:.1f} {X+side*52:.1f} {y-i*seg-8:.1f} Q{X+side*28:.1f} {y-i*seg-4:.1f} {X:.1f} {y-i*seg:.1f} Z" '
              f'fill="#5cb85c" stroke="{INK}" stroke-width="3"/>')
    return s


def bamboo_grove(X, y, h):
    return "".join(bamboo(X + dx, y, h * f, c) for dx, f, c in ((-34, 0.85, "#8bd47a"), (0, 1.0, "#7cc96a"), (30, 0.92, "#6dbd5c"), (58, 0.75, "#8bd47a")))


def panda(X, y, s_):
    return (blob([(X, y - s_ * 0.45, s_ * 0.45)], "#ffffff", sw=3)
            + f'<ellipse cx="{X-s_*0.32:.1f}" cy="{y-s_*0.1:.1f}" rx="{s_*0.18:.1f}" ry="{s_*0.12:.1f}" fill="#2b2b2b"/>'
            f'<ellipse cx="{X+s_*0.32:.1f}" cy="{y-s_*0.1:.1f}" rx="{s_*0.18:.1f}" ry="{s_*0.12:.1f}" fill="#2b2b2b"/>'
            + blob([(X, y - s_ * 1.05, s_ * 0.32)], "#ffffff", sw=3)
            + f'<circle cx="{X-s_*0.27:.1f}" cy="{y-s_*1.32:.1f}" r="{s_*0.11:.1f}" fill="#2b2b2b"/><circle cx="{X+s_*0.27:.1f}" cy="{y-s_*1.32:.1f}" r="{s_*0.11:.1f}" fill="#2b2b2b"/>'
            f'<ellipse cx="{X-s_*0.12:.1f}" cy="{y-s_*1.07:.1f}" rx="{s_*0.08:.1f}" ry="{s_*0.1:.1f}" fill="#2b2b2b"/><ellipse cx="{X+s_*0.12:.1f}" cy="{y-s_*1.07:.1f}" rx="{s_*0.08:.1f}" ry="{s_*0.1:.1f}" fill="#2b2b2b"/>'
            f'<circle cx="{X:.1f}" cy="{y-s_*0.95:.1f}" r="{s_*0.04:.1f}" fill="#2b2b2b"/>'
            f'<path d="M{X+s_*0.35:.1f} {y-s_*0.5:.1f} L{X+s_*0.75:.1f} {y-s_*0.95:.1f}" stroke="#7cc96a" stroke-width="7" stroke-linecap="round"/>')


def acacia(X, y, h):
    s = (f'<path d="M{X:.1f} {y:.1f} L{X:.1f} {y-h*0.55:.1f} M{X:.1f} {y-h*0.45:.1f} L{X-h*0.3:.1f} {y-h*0.78:.1f} M{X:.1f} {y-h*0.55:.1f} L{X+h*0.28:.1f} {y-h*0.8:.1f}" '
         f'fill="none" stroke="{INK}" stroke-width="{h*0.06+6:.1f}" stroke-linecap="round"/>'
         f'<path d="M{X:.1f} {y:.1f} L{X:.1f} {y-h*0.55:.1f} M{X:.1f} {y-h*0.45:.1f} L{X-h*0.3:.1f} {y-h*0.78:.1f} M{X:.1f} {y-h*0.55:.1f} L{X+h*0.28:.1f} {y-h*0.8:.1f}" '
         f'fill="none" stroke="#7a4b28" stroke-width="{h*0.06:.1f}" stroke-linecap="round"/>')
    s += (f'<path d="M{X-h*0.62:.1f} {y-h*0.82:.1f} Q{X-h*0.5:.1f} {y-h*1.02:.1f} {X:.1f} {y-h:.1f} Q{X+h*0.5:.1f} {y-h*1.02:.1f} {X+h*0.62:.1f} {y-h*0.82:.1f} '
          f'Q{X:.1f} {y-h*0.72:.1f} {X-h*0.62:.1f} {y-h*0.82:.1f} Z" fill="#6f9a3a" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    return s


def giraffe(X, y, h):
    c, sp = "#f2b84b", "#b8742d"
    s = "".join(f'<rect x="{X+dx:.1f}" y="{y-h*0.42:.1f}" width="9" height="{h*0.42:.1f}" fill="{c}" stroke="{INK}" stroke-width="3"/>' for dx in (-h*0.22, -h*0.14, h*0.1, h*0.18))
    s += f'<ellipse cx="{X:.1f}" cy="{y-h*0.48:.1f}" rx="{h*0.28:.1f}" ry="{h*0.12:.1f}" fill="{c}" stroke="{INK}" stroke-width="4"/>'
    s += f'<path d="M{X+h*0.18:.1f} {y-h*0.52:.1f} L{X+h*0.3:.1f} {y-h*0.95:.1f} L{X+h*0.38:.1f} {y-h*0.93:.1f} L{X+h*0.28:.1f} {y-h*0.5:.1f} Z" fill="{c}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
    s += f'<ellipse cx="{X+h*0.4:.1f}" cy="{y-h*0.96:.1f}" rx="{h*0.09:.1f}" ry="{h*0.05:.1f}" fill="{c}" stroke="{INK}" stroke-width="3"/>'
    s += f'<line x1="{X+h*0.33:.1f}" y1="{y-h*1.0:.1f}" x2="{X+h*0.33:.1f}" y2="{y-h*1.06:.1f}" stroke="{INK}" stroke-width="3"/>'
    for dx, dy in ((-0.12, 0.5), (0.05, 0.46), (0.15, 0.52), (0.26, 0.7), (0.3, 0.84), (-0.02, 0.53)):
        s += f'<circle cx="{X+dx*h:.1f}" cy="{y-dy*h:.1f}" r="{h*0.025:.1f}" fill="{sp}"/>'
    return s


def setting_sun(X, y, r):
    return (f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r*1.8:.1f}" fill="#fff1c4" opacity="0.25"/>'
            f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#ff9f43" opacity="0.9"/>')


def lavender_row(X, y, w):
    s = ""
    for i in range(int(w / 26)):
        x = X - w / 2 + i * 26 + 13
        s += blob([(x, y - 14, 13)], "#9c74d6", sw=2)
    return s


def lavender_bush(X, y, s_):
    out = blob([(X, y - s_ * 0.3, s_ * 0.45), (X - s_ * 0.45, y - s_ * 0.2, s_ * 0.32), (X + s_ * 0.45, y - s_ * 0.2, s_ * 0.32)], "#5f9a4f", sw=3)
    for dx, dy in ((-0.45, 0.7), (-0.15, 0.95), (0.15, 0.9), (0.45, 0.72), (0.0, 0.7)):
        out += f'<path d="M{X+dx*s_:.1f} {y-s_*0.35:.1f} L{X+dx*s_:.1f} {y-dy*s_:.1f}" stroke="#4a7a3d" stroke-width="3"/>'
        out += blob([(X + dx * s_, y - dy * s_ - 6, 7), (X + dx * s_, y - dy * s_ + 6, 6)], "#a77fe0", sw=2)
    return out


def cottage(X, y, w):
    h = w * 0.7
    return (f'<rect x="{X-w*0.4:.1f}" y="{y-h*0.6:.1f}" width="{w*0.8:.1f}" height="{h*0.6:.1f}" fill="#fff4e0" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{X-w*0.5:.1f} {y-h*0.58:.1f} L{X:.1f} {y-h:.1f} L{X+w*0.5:.1f} {y-h*0.58:.1f} Z" fill="#8a5cf6" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<rect x="{X-w*0.08:.1f}" y="{y-h*0.32:.1f}" width="{w*0.16:.1f}" height="{h*0.32:.1f}" fill="#7a4b28" stroke="{INK}" stroke-width="3"/>'
            f'<rect x="{X-w*0.32:.1f}" y="{y-h*0.48:.1f}" width="{w*0.14:.1f}" height="{w*0.12:.1f}" fill="#ffe680" stroke="{INK}" stroke-width="3"/>'
            f'<rect x="{X+w*0.18:.1f}" y="{y-h*0.48:.1f}" width="{w*0.14:.1f}" height="{w*0.12:.1f}" fill="#ffe680" stroke="{INK}" stroke-width="3"/>'
            f'<rect x="{X+w*0.2:.1f}" y="{y-h*0.95:.1f}" width="{w*0.1:.1f}" height="{h*0.22:.1f}" fill="#c0392b" stroke="{INK}" stroke-width="3"/>')


def skyscraper(X, y, w, h, c, lit="#ffe680", seed=0):
    import random as _r
    rr = _r.Random(seed + int(X))
    s = f'<rect x="{X-w/2:.1f}" y="{y-h:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{c}"/>'
    for row in range(int(h / 26)):
        for col in range(int(w / 20)):
            if rr.random() < 0.45:
                s += f'<rect x="{X-w/2+6+col*20:.1f}" y="{y-h+10+row*26:.1f}" width="9" height="12" fill="{lit}" opacity="0.85"/>'
    return s


def neon_sign(X, y, w, h, c):
    return (f'<rect x="{X-w/2:.1f}" y="{y-h:.1f}" width="{w:.1f}" height="{h:.1f}" rx="10" fill="#1d1236" stroke="{c}" stroke-width="6"/>'
            f'<rect x="{X-w/2-6:.1f}" y="{y-h-6:.1f}" width="{w+12:.1f}" height="{h+12:.1f}" rx="14" fill="none" stroke="{c}" stroke-width="10" opacity="0.25"/>'
            f'<path d="M{X-w*0.3:.1f} {y-h*0.3:.1f} L{X-w*0.1:.1f} {y-h*0.7:.1f} L{X+w*0.1:.1f} {y-h*0.3:.1f} L{X+w*0.3:.1f} {y-h*0.7:.1f}" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')

# ======================================================================= zones 2-22
class Z:
    """Builds one layer of a zone: terrain + elements, tracking edge spill."""

    def __init__(self, seed):
        self.rnd = random.Random(seed)
        self.els = []

    def add(self, x, ext, draw):
        self.els.append((x, ext, draw))

    def svg(self, carry):
        return "".join(d(x) for x, e, d in carry) + "".join(d(x) for x, e, d in self.els)

    def spill(self):
        return [(x - W, e, d) for x, e, d in self.els if x + e > W]


def place(rnd, n, lo=0, hi=W, avoid=(), min_gap=0):
    xs, tries = [], 0
    while len(xs) < n and tries < 2000:
        tries += 1
        x = rnd.uniform(lo, hi)
        if any(a < x < b for a, b in avoid) or any(abs(x - o) < min_gap for o in xs):
            continue
        xs.append(x)
    return sorted(xs)


def sky_layer(zone):
    z = Z(100 + zone)
    if zone in (17, 22):                 # night: stars and a moon instead of clouds
        for _ in range(40):
            x, y = z.rnd.uniform(10, W - 10), z.rnd.uniform(20, 560)
            z.add(x, 8, lambda X, y=y, r=z.rnd.uniform(1.5, 3.5): f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#fff7c2"/>')
        z.add(1400 if zone == 17 else 500, 120, lambda X: moon(X, 170, 70 if zone == 17 else 55))
        return sky_defs(zone), "", z
    for i in range(4):
        x = i * W / 4 + z.rnd.uniform(60, 300)
        y, sc = z.rnd.uniform(90, 400), z.rnd.uniform(0.7, 1.25)
        if zone == 16:
            z.add(x, 182 * sc, lambda X, y=y, sc=sc: blob([(X + a * sc, y + b * sc, r * sc) for a, b, r in CLOUD_PARTS], "#ffe3f1", stroke="#f7b6d6", sw=3))
        else:
            z.add(x, 182 * sc, lambda X, y=y, sc=sc: cloud(X, y, sc))
    return sky_defs(zone), "", z


ZONES = {
    2: dict(name="rocky_highlands", label="Rocky Highlands", dist="100 yd",
            mtn=dict(extra=[(40, 4, 0.7), (20, 9, 2.0)], lift=-30),
            hills=dict(extra=[(18, 4, 1.2)], lift=-10),
            trees=dict(extra=[(14, 5, 0.3)], lift=0)),
    3: dict(name="ancient_ruins", label="Ancient Ruins", dist="200 yd",
            mtn=dict(extra=[(25, 3, 1.0)], lift=10),
            hills=dict(extra=[(12, 3, 0.4)], lift=5),
            trees=dict(extra=[(8, 4, 2.0)], lift=10)),
    4: dict(name="jungle_temple", label="Jungle Temple", dist="300 yd",
            mtn=dict(extra=[(30, 5, 0.2)], lift=-10),
            hills=dict(extra=[(15, 6, 1.1)], lift=-15),
            trees=dict(extra=[(10, 3, 0.9)], lift=15)),
    5: dict(name="mountain_shrine", label="Mountain Shrine", dist="400 yd",
            mtn=dict(extra=[(50, 3, 1.6), (25, 7, 0.4)], lift=-50),
            hills=dict(extra=[(20, 3, 2.4)], lift=-20),
            trees=dict(extra=[(12, 4, 1.5)], lift=0)),
    6: dict(name="mystic_stones", label="Mystic Stones", dist="500 yd",
            mtn=dict(extra=[(20, 4, 2.2)], lift=-20),
            hills=dict(extra=[(14, 5, 0.6)], lift=-5),
            trees=dict(extra=[(9, 3, 2.6)], lift=5)),
    7: dict(name="sunny_coast", label="Sunny Coast", dist="600 yd",
            mtn=dict(extra=[(20, 3, 0.5)], lift=40),
            hills=dict(extra=[(12, 4, 1.7)], lift=10),
            trees=dict(extra=[(8, 3, 0.2)], lift=8)),
    8: dict(name="windmill_farm", label="Windmill Farm", dist="700 yd",
            mtn=dict(extra=[(18, 2, 1.1)], lift=20),
            hills=dict(extra=[(16, 3, 0.9)], lift=0),
            trees=dict(extra=[(10, 4, 1.9)], lift=0)),
    9: dict(name="autumn_woods", label="Autumn Woods", dist="800 yd",
            mtn=dict(extra=[(30, 4, 2.0)], lift=-10),
            hills=dict(extra=[(14, 5, 0.3)], lift=-8),
            trees=dict(extra=[(10, 3, 1.2)], lift=5)),
    10: dict(name="volcano_ridge", label="Volcano Ridge", dist="900 yd",
             mtn=dict(extra=[(40, 3, 2.8), (20, 6, 1.0)], lift=-30),
             hills=dict(extra=[(18, 4, 0.5)], lift=-12),
             trees=dict(extra=[(12, 5, 2.2)], lift=0)),
    11: dict(name="sky_isles", label="Sky Isles", dist="1000 yd",
             mtn=dict(extra=[(16, 2, 0.7)], lift=10),
             hills=dict(extra=[(14, 3, 1.4)], lift=0),
             trees=dict(extra=[(8, 4, 0.8)], lift=5)),
    12: dict(name="royal_castle", label="Royal Castle", dist="1100 yd",
             mtn=dict(extra=[(22, 3, 1.3)], lift=0),
             hills=dict(extra=[(10, 2, 2.0)], lift=0),
             trees=dict(extra=[(6, 3, 0.6)], lift=12)),
    13: dict(name="frozen_peaks", label="Frozen Peaks", dist="1200 yd",
             mtn=dict(extra=[(50, 3, 0.4), (25, 7, 1.8)], lift=-50),
             hills=dict(extra=[(18, 4, 2.1)], lift=-10),
             trees=dict(extra=[(10, 3, 0.7)], lift=0)),
    14: dict(name="desert_oasis", label="Desert Oasis", dist="1300 yd",
             mtn=dict(extra=[(24, 2, 1.5)], lift=20),
             hills=dict(extra=[(16, 3, 0.2)], lift=5),
             trees=dict(extra=[(8, 4, 1.4)], lift=5)),
    15: dict(name="mushroom_grove", label="Mushroom Grove", dist="1400 yd",
             mtn=dict(extra=[(20, 4, 0.9)], lift=0),
             hills=dict(extra=[(14, 5, 1.6)], lift=-5),
             trees=dict(extra=[(9, 3, 2.4)], lift=5)),
    16: dict(name="candy_land", label="Candy Land", dist="1500 yd",
             mtn=dict(extra=[(26, 3, 2.6)], lift=0),
             hills=dict(extra=[(12, 4, 0.8)], lift=0),
             trees=dict(extra=[(8, 3, 1.1)], lift=8)),
    17: dict(name="starlight_summit", label="Starlight Summit", dist="1600 yd",
             mtn=dict(extra=[(40, 3, 1.2), (18, 6, 0.3)], lift=-30),
             hills=dict(extra=[(16, 3, 2.7)], lift=-8),
             trees=dict(extra=[(10, 4, 0.5)], lift=0)),
    18: dict(name="coral_lagoon", label="Coral Lagoon", dist="1700 yd",
             mtn=dict(extra=[(18, 2, 0.6)], lift=45),
             hills=dict(extra=[(10, 4, 1.2)], lift=10),
             trees=dict(extra=[(6, 3, 0.4)], lift=10)),
    19: dict(name="bamboo_forest", label="Bamboo Forest", dist="1800 yd",
             mtn=dict(extra=[(45, 3, 2.1), (20, 7, 0.6)], lift=-40),
             hills=dict(extra=[(16, 4, 1.0)], lift=-10),
             trees=dict(extra=[(10, 3, 2.3)], lift=0)),
    20: dict(name="golden_savanna", label="Golden Savanna", dist="1900 yd",
             mtn=dict(extra=[(14, 2, 1.8)], lift=30),
             hills=dict(extra=[(8, 3, 0.5)], lift=10),
             trees=dict(extra=[(6, 2, 1.6)], lift=10)),
    21: dict(name="lavender_fields", label="Lavender Fields", dist="2000 yd",
             mtn=dict(extra=[(22, 3, 0.9)], lift=10),
             hills=dict(extra=[(14, 3, 2.2)], lift=0),
             trees=dict(extra=[(9, 4, 0.3)], lift=5)),
    22: dict(name="neon_city", label="Neon City", dist="2100 yd",
             mtn=dict(extra=[(10, 2, 0.4)], lift=20),
             hills=dict(extra=[(8, 3, 1.5)], lift=0),
             trees=dict(extra=[(6, 4, 2.0)], lift=8)),
}


def mountains_layer(zone, cfg):
    z = Z(200 + zone)
    yb = make_yf(T_MTN_BACK, cfg["mtn"]["extra"], cfg["mtn"]["lift"])
    yfr = make_yf(T_MTN_FRONT, [(a * 0.7, k + 1, p) for a, k, p in cfg["mtn"]["extra"]], cfg["mtn"]["lift"] * 0.6)
    sil = "#8dd2b2"
    if zone == 2:
        for x in (520, 820, 1300, 1560):
            z.add(x, 150, lambda X: far_peak(X, yfr(X) + 30, 300, 230 + (X % 70), "#9fb7b9", snow=True))
    elif zone == 3:
        z.add(1250, 130, lambda X: far_colonnade(X, yb(X) + 25, 240, 90, sil))
    elif zone == 4:
        z.add(1300, 210, lambda X: far_ziggurat(X, yfr(X) + 40, 400, 250, "#86c9a6"))
        z.add(500, 120, lambda X: far_ziggurat(X, yfr(X) + 30, 220, 130, "#86c9a6"))
    elif zone == 5:
        for x, h in ((450, 300), (760, 380), (1150, 330), (1500, 400)):
            z.add(x, 190, lambda X, h=h: far_peak(X, yfr(X) + 40, 380, h, "#93c9b4", snow=True))
    elif zone == 6:
        for x, w, h in ((480, 300, 170), (1000, 380, 220), (1480, 260, 150)):
            z.add(x, w / 2 + 5, lambda X, w=w, h=h: far_mesa(X, yfr(X) + 30, w, h, "#8fc9b8"))
    elif zone == 7:
        z.add(980, 700, lambda X: bay(X, yfr(X) + 30, 1300, 120))
    elif zone == 8:
        for x, h in ((520, 140), (1500, 120)):
            z.add(x, 80, lambda X, h=h: windmill(X, yfr(X) + 20, h, rot=30))
    elif zone == 9:
        for x, h in ((600, 260), (1300, 300)):
            z.add(x, 170, lambda X, h=h: far_peak(X, yfr(X) + 40, 340, h, "#c9b48f"))
    elif zone == 10:
        z.add(1000, 380, lambda X: volcano(X, yfr(X) + 40, 760, 380))
        for x in (380, 1620):
            z.add(x, 150, lambda X: far_peak(X, yfr(X) + 30, 300, 200, "#8a948f"))
    elif zone == 11:
        z.add(960, 560, lambda X: rainbow(X, yfr(X) + 30, 540))
        for x, yy, s_ in ((420, 300, 50), (1500, 260, 60)):
            z.add(x, 70, lambda X, yy=yy, s_=s_: float_isle(X, yy, s_, tree=False))
    elif zone == 12:
        for x, h in ((520, 220), (1450, 250)):
            z.add(x, 140, lambda X, h=h: far_peak(X, yfr(X) + 30, 280, h, "#93c9b4", snow=True))
    elif zone == 13:
        for x, h in ((380, 320), (760, 420), (1180, 360), (1560, 440)):
            z.add(x, 200, lambda X, h=h: far_peak(X, yfr(X) + 40, 400, h, "#cfe0ec", snow=True))
    elif zone == 14:
        z.add(700, 230, lambda X: pyramid(X, yfr(X) + 30, 420, 260, "#e7c88e"))
        z.add(1150, 150, lambda X: pyramid(X, yfr(X) + 30, 280, 170, "#ddb979"))
    elif zone == 15:
        for x, h, c in ((500, 260, "#c6a4ee"), (1400, 300, "#b493e6")):
            z.add(x, h * 0.5, lambda X, h=h, c=c: giant_mushroom(X, yfr(X) + 40, h, c, "#e9dcff"))
    elif zone == 16:
        for x, h in ((450, 300), (980, 360), (1500, 320)):
            z.add(x, 190, lambda X, h=h: far_peak(X, yfr(X) + 40, 380, h, "#f7a8c8", snow=True))
    elif zone == 17:
        for x, h in ((420, 300), (900, 380), (1450, 340)):
            z.add(x, 190, lambda X, h=h: far_peak(X, yfr(X) + 40, 380, h, "#3a3f7a", snow=True))
    elif zone == 18:
        z.add(960, 700, lambda X: bay(X, yfr(X) + 30, 1500, 140, "#2fd0d6"))
        for x, w in ((520, 180), (1420, 240)):
            z.add(x, w / 2 + 5, lambda X, w=w: far_mesa(X, yfr(X) - 70, w, 40, "#7fcf9a"))
    elif zone == 19:
        for x, h in ((380, 330), (720, 420), (1100, 360), (1500, 440)):
            z.add(x, 200, lambda X, h=h: far_peak(X, yfr(X) + 40, 360, h, "#a6d4b2"))
    elif zone == 20:
        z.add(1350, 260, lambda X: setting_sun(X, yfr(X) - 60, 130))
        for x, w, h in ((500, 320, 120), (1000, 260, 90)):
            z.add(x, w / 2 + 5, lambda X, w=w, h=h: far_mesa(X, yfr(X) + 30, w, h, "#d99a5b"))
    elif zone == 21:
        for x, h in ((600, 80), (1400, 90)):
            z.add(x, 50, lambda X, h=h: windmill(X, yfr(X) + 20, h, rot=10))
    elif zone == 22:
        for i, x in enumerate(range(140, 1900, 120)):
            hh = 180 + (i * 53) % 170
            z.add(x, 60, lambda X, hh=hh, i=i: skyscraper(X, yfr(X) + 40, 100, hh, "#2a1a52", "#c9a6ff", seed=i))
    pre = layer_defs(zone, ("mb", "mb"), ("mf", "mf")) + f'<path d="{gpath(yb)}" fill="url(#mb)"/>'
    post = f'<path d="{gpath(yfr)}" fill="url(#mf)"/>'
    return pre, post, z


def hills_layer(zone, cfg):
    z = Z(300 + zone)
    yf = make_yf(T_HILLS, cfg["hills"]["extra"], cfg["hills"]["lift"])
    r_ = z.rnd
    shades = {2: ["#3fae58", "#4aa868"], 3: ["#3fae58", "#48b960"], 4: ["#249344", "#2ea84e", "#1f8a45"],
              5: ["#3fae58", "#ffb3d1", "#ff9ec4"], 6: ["#3fae58", "#5fc5a0"], 7: ["#3fae58", "#5cc46a"],
              8: ["#3fae58", "#69c26a"], 9: ["#e8913a", "#d9673a", "#f2b33d"], 10: ["#3a8f56", "#4f6b5c"],
              11: ["#3fae58", "#5fc5a0"], 12: ["#3fae58", "#48b960"], 13: ["#ffffff", "#e3eef5"],
              14: ["#c9a85e", "#4caf62"], 15: ["#ff6b6b", "#8a5cf6", "#4cc3f0"], 16: ["#f7a8c8", "#ffe14d", "#7ef0c0"],
              17: ["#245548", "#2c6655"], 18: ["#2fa86a", "#ff8fa3"], 19: ["#5cb85c", "#4ea867"],
              20: ["#a8b84a", "#c9a24a"], 21: ["#9c74d6", "#b494e1"], 22: ["#2a1a52", "#3a2566"]}[zone]
    avoid = {2: [(980, 1240)], 3: [(820, 1080)], 4: [(380, 640)], 5: [(1280, 1440)], 6: [(860, 1140)],
             7: [(1350, 1560)], 8: [(480, 760)], 9: [], 10: [(700, 1300)], 11: [(800, 1200)], 12: [(500, 1500)],
             13: [(880, 1120)], 14: [(840, 1160)], 15: [], 16: [], 17: [(1180, 1420)],
             18: [(1300, 1560)], 19: [], 20: [], 21: [(700, 1300)], 22: [(0, 1920)]}[zone]
    count = 20 if zone == 4 else 12
    for x in place(r_, count, avoid=avoid, min_gap=30):
        y = yf(x) + 6
        rr = r_.uniform(16, 28) * (1.25 if zone == 4 else 1)
        c = r_.choice(shades)
        z.add(x, rr * 1.7 + 4, lambda X, y=y, rr=rr, c=c: blob([(X, y - rr, rr), (X - rr * .7, y - rr * .5, rr * .7), (X + rr * .7, y - rr * .5, rr * .7)], c, sw=3))
    if zone == 2:
        z.add(1110, 110, lambda X: rock_arch(X, yf(X) + 8, 90))
        for x in (300, 700, 1500, 1750):
            z.add(x, 40, lambda X: boulder(X, yf(X) + 6, 70, 48))
    elif zone == 3:
        def colonnade(X):
            y = yf(X) + 6
            s = "".join(column(X - 100 + i * 50, y, 92 - (30 if i == 3 else 0), broken=(i == 3), w=20) for i in range(5))
            return f'<rect x="{X-118:.1f}" y="{y-104:.1f}" width="166" height="14" rx="3" fill="{STONE_D}" stroke="{INK}" stroke-width="4"/>' + s
        z.add(950, 130, colonnade)
    elif zone == 4:
        z.add(510, 130, lambda X: ziggurat(X, yf(X) + 8, 230, 150, steps=4))
    elif zone == 5:
        z.add(1360, 70, lambda X: pagoda(X, yf(X) + 8, 220))
    elif zone == 6:
        def ring(X):
            y = yf(X) + 6
            return "".join(standing_stone(X + dx, y, 22, 60 + (dx % 3) * 6) for dx in (-110, -66, -22, 22, 66, 110))
        z.add(1000, 130, ring)
    elif zone == 7:
        z.add(1450, 50, lambda X: lighthouse(X, yf(X) + 8, 240))
    elif zone == 8:
        z.add(620, 120, lambda X: barn(X, yf(X) + 8, 210, 160))
        z.add(1000, 140, lambda X: fence(X, yf(X) + 8, 260))
    elif zone == 10:
        for x in (450, 1450, 1700):
            z.add(x, 45, lambda X: lava_rock(X, yf(X) + 6, 80, 54))
    elif zone == 11:
        z.add(1000, 120, lambda X: float_isle(X, yf(X) - 170, 90))
    elif zone == 12:
        z.add(1000, 460, lambda X: pennant_line(X, yf(X) - 60, 900))
    if zone == 18:
        z.add(1430, 90, lambda X: stilt_hut(X, yf(X) + 8, 150))
        for x, c in ((420, "#ff8fa3"), (900, "#ffb02e")):
            z.add(x, 50, lambda X, c=c: coral(X, yf(X) + 6, 60, c))
    elif zone == 19:
        for x in (300, 900, 1500):
            z.add(x, 90, lambda X: bamboo_grove(X, yf(X) + 8, 170))
    elif zone == 20:
        for x, h in ((450, 140), (1200, 120), (1700, 150)):
            z.add(x, h * 0.65, lambda X, h=h: acacia(X, yf(X) + 6, h))
    elif zone == 21:
        for k in range(5):
            z.add(1000, 320, lambda X, k=k: lavender_row(X, yf(X) + 6 + k * 14, 560))
    elif zone == 22:
        for i, x in enumerate(range(80, 1920, 170)):
            hh = 160 + (i * 71) % 150
            col = ["#4a2f7a", "#3d2a66", "#57388c"][i % 3]
            z.add(x, 70, lambda X, hh=hh, col=col, i=i: skyscraper(X, yf(X) + 8, 130, hh, col, "#ffe680", seed=100 + i))
    elif zone == 13:
        z.add(1000, 90, lambda X: igloo(X, yf(X) + 8, 150))
    elif zone == 14:
        z.add(1000, 220, lambda X: oasis(X, yf(X) + 6, 300) + palm(X - 110, yf(X) + 4, 150, 1) + palm(X + 120, yf(X) + 4, 130, -1))
    elif zone == 17:
        z.add(1300, 90, lambda X: observatory(X, yf(X) + 8, 150))
    pre = layer_defs(zone, ("hl", "hills")) + f'<path d="{gpath(yf)}" fill="url(#hl)"/>' + gridge(yf, 5)
    return pre, "", z


def trees_layer(zone, cfg):
    z = Z(400 + zone)
    yf = make_yf(T_TREES, cfg["trees"]["extra"], cfg["trees"]["lift"])
    r_ = z.rnd

    def add_round(x, c=None, trunk="#8a5a32", hr=(110, 180)):
        h = r_.uniform(*hr)
        c = c or r_.choice(["#2ea84e", "#249344", "#38b85a"])
        z.add(x, h * 0.56 + 5, lambda X, h=h, c=c: round_tree(X, yf(X) + 10, h, c, trunk))

    def add_pine(x):
        h = r_.uniform(120, 190)
        z.add(x, h * 0.42 + 5, lambda X, h=h: pine_tree(X, yf(X) + 10, h, "#1f8a45", "#26a052"))

    if zone == 2:
        z.add(700, 175, lambda X: cliff(X, yf(X) + 12, 340, 230))
        for x, w, h, m in ((260, 150, 100, True), (1080, 190, 130, True), (1290, 120, 80, False), (1640, 160, 110, True)):
            z.add(x, w * 0.6, lambda X, w=w, h=h, m=m: boulder(X, yf(X) + 12, w, h, moss=m))
        for x in place(r_, 4, avoid=[(520, 880), (980, 1380)], min_gap=140):
            add_pine(x)
    elif zone == 3:
        z.add(1130, 150, lambda X: stone_arch(X, yf(X) + 12, 280, 300))
        for x, h, b in ((420, 260, False), (520, 200, True), (760, 240, False), (1460, 170, True), (1560, 250, False)):
            z.add(x, 30, lambda X, h=h, b=b: column(X, yf(X) + 12, h, broken=b))
        z.add(1760, 115, lambda X: ruin_wall(X, yf(X) + 12, 220, 120))
        z.add(220, 115, lambda X: ruin_wall(X, yf(X) + 12, 200, 90))
        for x in place(r_, 2, avoid=[(380, 820), (960, 1310), (1420, 1600)], min_gap=200):
            add_round(x)
    elif zone == 4:
        z.add(1000, 270, lambda X: ziggurat(X, yf(X) + 14, 520, 390))
        for x, h, lean in ((300, 230, 1), (560, 260, -1), (1400, 250, 1), (1620, 210, -1), (1820, 240, 1)):
            z.add(x, h * 0.62, lambda X, h=h, lean=lean: palm(X, yf(X) + 12, h, lean))
        for x in place(r_, 2, avoid=[(700, 1300)], min_gap=200):
            add_round(x, c=r_.choice(["#1f8a45", "#249344"]))
    elif zone == 5:
        z.add(820, 190, lambda X: gate(X, yf(X) + 12, 320, 260))
        for x in (590, 1050):
            z.add(x, 35, lambda X: lantern(X, yf(X) + 12, 110))
        for x in (300, 1250, 1560):
            add_round(x, c=r_.choice(["#ffb3d1", "#ff9ec4"]), trunk="#6e4426", hr=(130, 190))
        for x in (120, 1720):
            add_pine(x)
    elif zone == 6:
        def circle(X):
            y = yf(X) + 12
            return (standing_stone(X - 250, y, 60, 170) + trilithon(X, y, 230, 230)
                    + standing_stone(X + 250, y, 60, 190) + standing_stone(X - 360, y, 50, 120) + standing_stone(X + 360, y, 50, 130))
        z.add(1000, 400, circle)
        for x, s_, c, c2 in ((400, 50, "#b98cff", "#e2ccff"), (1530, 60, "#6fe3ff", "#d2f8ff"), (1780, 40, "#b98cff", "#e2ccff")):
            z.add(x, s_ * 1.2, lambda X, s_=s_, c=c, c2=c2: crystals(X, yf(X) + 12, s_, c, c2))
        for x in (200, 1680):
            add_round(x, c=r_.choice(["#2fb08a", "#38b8a0"]))
        for x in (640, 1420):
            z.add(x, 30, lambda X: mushroom(X, yf(X) + 12, 40))
    elif zone == 7:
        for x, h, lean in ((260, 230, 1), (700, 260, -1), (1250, 240, 1), (1700, 220, -1)):
            z.add(x, h * 0.62, lambda X, h=h, lean=lean: palm(X, yf(X) + 12, h, lean))
        for x, c1, c2 in ((480, "#ff6b6b", "#ffffff"), (980, "#4cc3f0", "#ffe14d"), (1480, "#ffb02e", "#ffffff")):
            z.add(x, 60, lambda X, c1=c1, c2=c2: umbrella(X, yf(X) + 12, 70, c1, c2))
    elif zone == 8:
        z.add(1150, 180, lambda X: windmill(X, yf(X) + 12, 340))
        for x, r in ((480, 34), (560, 28), (1600, 32)):
            z.add(x, r + 6, lambda X, r=r: hay_bale(X, yf(X) + 12, r))
        for x in (250, 1780):
            add_round(x)
        z.add(820, 110, lambda X: fence(X, yf(X) + 12, 200))
    elif zone == 9:
        for x in (180, 450, 760, 1100, 1380, 1700):
            add_round(x, c=r_.choice(["#e8913a", "#d9673a", "#f2b33d", "#c9622e"]), trunk="#6e4426", hr=(130, 200))
        for x in (930, 1560):
            add_pine(x)
    elif zone == 10:
        for x, h in ((300, 150), (820, 130), (1550, 160)):
            z.add(x, h * 0.3, lambda X, h=h: burnt_tree(X, yf(X) + 12, h))
        for x, w, h in ((560, 160, 110), (1200, 200, 130), (1800, 140, 90)):
            z.add(x, w * 0.6, lambda X, w=w, h=h: lava_rock(X, yf(X) + 12, w, h))
    elif zone == 11:
        z.add(1000, 180, lambda X: float_isle(X, yf(X) - 330, 140))
        for x in (300, 1650):
            add_round(x, c="#38b8a0")
        for x, s_ in ((620, 46), (1380, 54)):
            z.add(x, s_ * 1.2, lambda X, s_=s_: crystals(X, yf(X) + 12, s_, "#6fe3ff", "#d2f8ff"))
    elif zone == 12:
        z.add(1000, 380, lambda X: castle(X, yf(X) + 14, 720, 400))
        for x, c in ((420, "#e2483a"), (1580, "#4a7bd9")):
            z.add(x, 50, lambda X, c=c: banner_pole(X, yf(X) + 12, 230, c))
        for x in (180, 1800):
            add_round(x)
    if zone == 18:
        for x, h, lean in ((260, 220, 1), (1150, 240, -1), (1760, 210, 1)):
            z.add(x, h * 0.62, lambda X, h=h, lean=lean: palm(X, yf(X) + 12, h, lean))
        for x, s_, c in ((560, 90, "#ff6b8a"), (820, 70, "#ffb02e"), (1450, 100, "#c96bff")):
            z.add(x, s_ * 1.3, lambda X, s_=s_, c=c: coral(X, yf(X) + 12, s_, c))
        for x in (660, 1320, 1580):
            z.add(x, 30, lambda X: seaweed(X, yf(X) + 12, 110))
    elif zone == 19:
        for x in (180, 640, 1120, 1600):
            z.add(x, 100, lambda X: bamboo_grove(X, yf(X) + 12, 300))
        z.add(880, 70, lambda X: panda(X, yf(X) + 12, 70))
        z.add(1380, 40, lambda X: lantern(X, yf(X) + 12, 100))
    elif zone == 20:
        for x, h in ((260, 220), (980, 260), (1700, 200)):
            z.add(x, h * 0.65, lambda X, h=h: acacia(X, yf(X) + 12, h))
        for x, h in ((620, 230), (1350, 200)):
            z.add(x, h * 0.45, lambda X, h=h: giraffe(X, yf(X) + 12, h))
    elif zone == 21:
        z.add(1000, 120, lambda X: cottage(X, yf(X) + 12, 200))
        for x in (220, 440, 680, 1300, 1520, 1760):
            z.add(x, 60, lambda X: lavender_bush(X, yf(X) + 12, 80))
    elif zone == 22:
        for x in (200, 560, 920, 1280, 1640):
            z.add(x, 30, lambda X: glow_lamp(X, yf(X) + 12, 130))
        for x, c in ((380, "#ff4fd8"), (1100, "#4ff0ff"), (1460, "#ffe14d")):
            z.add(x, 70, lambda X, c=c: neon_sign(X, yf(X) - 60, 120, 70, c))
        for x in (740, 1820):
            add_round(x, c="#2f8a6f")
    elif zone == 13:
        for x, h in ((200, 170), (520, 200), (1300, 190), (1650, 160), (1820, 140)):
            z.add(x, h * 0.42 + 5, lambda X, h=h: snow_pine(X, yf(X) + 10, h))
        z.add(950, 80, lambda X: snowman(X, yf(X) + 12, 90))
        for x, s_ in ((760, 40), (1120, 50)):
            z.add(x, s_ * 1.2, lambda X, s_=s_: crystals(X, yf(X) + 12, s_, "#9fdcff", "#e6f6ff"))
    elif zone == 14:
        for x, h in ((260, 170), (640, 210), (1240, 190), (1560, 150)):
            z.add(x, h * 0.35, lambda X, h=h: cactus(X, yf(X) + 12, h))
        for x, w, h in ((900, 140, 80), (1800, 120, 70)):
            z.add(x, w * 0.6, lambda X, w=w, h=h: boulder(X, yf(X) + 12, w, h, c="#d9b98a"))
    elif zone == 15:
        for x, h, c in ((240, 220, "#ff6b6b"), (620, 280, "#8a5cf6"), (1050, 240, "#4cc3f0"), (1420, 300, "#ff6b6b"), (1760, 200, "#ffb02e")):
            z.add(x, h * 0.46, lambda X, h=h, c=c: giant_mushroom(X, yf(X) + 12, h, c))
        for _ in range(10):
            x, yy = r_.uniform(60, W - 60), r_.uniform(450, 720)
            c = r_.choice(["#7ef0ff", "#c9a6ff", "#fff38a"])
            z.add(x, 12, lambda X, yy=yy, c=c: spore(X, yy, c))
    elif zone == 16:
        for x, h, c1, c2 in ((220, 220, "#ff6b6b", "#ffffff"), (720, 260, "#7ef0c0", "#ff8fc7"), (1280, 240, "#ffe14d", "#ff6b6b"), (1720, 200, "#c9a6ff", "#ffffff")):
            z.add(x, h * 0.3, lambda X, h=h, c1=c1, c2=c2: lollipop(X, yf(X) + 12, h, c1, c2))
        for x in (480, 1500):
            z.add(x, 40, lambda X: candy_cane(X, yf(X) + 12, 180))
        for x in (980, 1080):
            z.add(x, 40, lambda X: cupcake(X, yf(X) + 12, 80))
    elif zone == 17:
        for x in (200, 560, 900, 1650):
            h = r_.uniform(150, 200)
            z.add(x, h * 0.42 + 5, lambda X, h=h: pine_tree(X, yf(X) + 10, h, "#1d4d42", "#245a4d"))
        for x in (380, 760, 1180, 1480, 1820):
            z.add(x, 30, lambda X: glow_lamp(X, yf(X) + 12, 120))
        for _ in range(12):
            x, yy = r_.uniform(60, W - 60), r_.uniform(500, 760)
            z.add(x, 12, lambda X, yy=yy: firefly(X, yy))
    pre = layer_defs(zone, ("tr", "trees")) + f'<path d="{gpath(yf)}" fill="url(#tr)"/>' + gridge(yf, 5)
    return pre, "", z


def ground_layer(zone, cfg):
    z = Z(500 + zone)
    base, terms = T_GROUND
    yf = make_yf(T_GROUND)          # ground line identical everywhere -> easy for gameplay collision
    r_ = z.rnd
    bush_c = {4: "#1f8a45", 6: "#2fa48a", 9: "#c9622e", 10: "#3a7a50", 11: "#2fa48a", 13: "#e9f2f8", 14: "#b9a05a",
              16: "#f7a8c8", 17: "#245548", 18: "#2fa86a", 20: "#a8a040", 21: "#8f6cc9", 22: "#2a5a55"}.get(zone, "#2fa44f")
    for x in place(r_, 4, lo=60, hi=W - 60, avoid=[(860, 1060)], min_gap=260):
        rr = r_.uniform(24, 38)
        z.add(x, rr * 1.8 + 6, lambda X, rr=rr: bush(X, yf(X) + 8, rr, bush_c))
    if SIGNS:
        z.add(960, 75, lambda X: sign(X, yf(X) + 40, cfg["dist"]))
    for _ in range(20):
        x, y = r_.uniform(20, W - 20), r_.uniform(base + 30, H - 20)
        k = r_.random()
        if k < 0.35:
            if zone == 9:
                z.add(x, 8, lambda X, y=y, rot=r_.uniform(0, 180), c=r_.choice(["#e8913a", "#d9673a", "#f2b33d"]): leaf(X, y, rot, c))
            elif zone == 10:
                z.add(x, 17, lambda X, y=y: pebble_dark(X, y))
            elif zone == 7:
                z.add(x, 14, lambda X, y=y, c=r_.choice(["#ffd1dc", "#fff1c9", "#ffffff"]): shell(X, y, c))
            elif zone == 13:
                z.add(x, 17, lambda X, y=y: snow_lump(X, y))
            elif zone == 18:
                z.add(x, 14, lambda X, y=y, c=r_.choice(["#ff8fa3", "#ffb02e", "#ff6b6b"]): starfish(X, y, 12, c))
            elif zone == 21:
                z.add(x, 14, lambda X, y=y: blob([(X, y - 6, 6), (X, y + 4, 5)], "#a77fe0", sw=2))
            elif zone == 16:
                z.add(x, 8, lambda X, y=y, rot=r_.uniform(0, 180), c=r_.choice(["#ff6b6b", "#ffe14d", "#4cc3f0", "#7ef0c0", "#c9a6ff"]): sprinkle(X, y, rot, c))
            elif zone in (17, 22):
                z.add(x, 12, lambda X, y=y: firefly(X, y))
            elif zone in (5, 12):
                z.add(x, 8, lambda X, y=y, rot=r_.uniform(0, 180): petal(X, y, rot))
            elif zone in (6, 11, 15):
                z.add(x, 14, lambda X, y=y: glow_flower(X, y))
            else:
                c = r_.choice(["#ffffff", "#ffe14d", "#ff8fc7", "#ff6b6b", "#b98cff"])
                z.add(x, 13, lambda X, y=y, c=c: flower(X, y, c))
        elif k < 0.75:
            z.add(x, 13, lambda X, y=y: tuft(X, y))
        else:
            z.add(x, 17, lambda X, y=y: pebble(X, y))
    if zone == 2:
        for x in (330, 1240, 1600):
            y = r_.uniform(base + 70, H - 40)
            z.add(x, 50, lambda X, y=y: boulder(X, y, 90, 60, moss=True))
    elif zone == 3:
        for x in (420, 1450):
            y = r_.uniform(base + 80, H - 40)
            z.add(x, 60, lambda X, y=y: drum(X, y, 50))
        for i in range(8):
            z.add(620 + i * 70, 40, lambda X, i=i: tile(X, 1060 - (i % 2) * 6, 34))
    elif zone == 4:
        for x in place(r_, 5, lo=60, hi=W - 60, min_gap=200):
            y = r_.uniform(base + 60, H - 20)
            z.add(x, 40, lambda X, y=y: fern(X, y, 42))
        for x in (700, 1300):
            y = r_.uniform(base + 80, H - 40)
            z.add(x, 50, lambda X, y=y: ruin_wall(X, y, 80, 44))
    elif zone == 5:
        for i in range(6):
            z.add(360 + i * 200, 40, lambda X, i=i: stepping_stone(X, 1010 + (i % 2) * 22, 34))
        z.add(1700, 30, lambda X: lantern(X, 1040, 90))
    elif zone == 6:
        for x in place(r_, 3, lo=60, hi=W - 60, avoid=[(880, 1040)], min_gap=300):
            y = r_.uniform(base + 70, H - 30)
            c, c2 = r_.choice([("#b98cff", "#e2ccff"), ("#6fe3ff", "#d2f8ff")])
            z.add(x, 30, lambda X, y=y, c=c, c2=c2: crystals(X, y, 22, c, c2))
        for x in (520, 1500):
            y = r_.uniform(base + 70, H - 30)
            z.add(x, 22, lambda X, y=y: mushroom(X, y, 28))
    elif zone == 8:
        for x in (420, 1500):
            y = r_.uniform(base + 80, H - 30)
            z.add(x, 30, lambda X, y=y: hay_bale(X, y, 24))
    elif zone == 9:
        for x in (380, 1250, 1650):
            y = r_.uniform(base + 80, H - 30)
            z.add(x, 40, lambda X, y=y: pumpkin(X, y, 44))
    elif zone == 10:
        for x in (500, 1400):
            y = r_.uniform(base + 80, H - 30)
            z.add(x, 50, lambda X, y=y: lava_rock(X, y, 80, 50))
    elif zone == 12:
        for i in range(6):
            z.add(360 + i * 220, 40, lambda X, i=i: stepping_stone(X, 1015 + (i % 2) * 20, 36))
    elif zone == 14:
        for x in (420, 1380):
            y = r_.uniform(base + 80, H - 30)
            z.add(x, 30, lambda X, y=y: cactus(X, y, 70))
    elif zone == 15:
        for x in (500, 1300, 1700):
            y = r_.uniform(base + 70, H - 30)
            z.add(x, 22, lambda X, y=y: mushroom(X, y, 32))
    elif zone == 16:
        for x, c in ((450, "#ff6b6b"), (1250, "#7ef0c0"), (1650, "#ffe14d")):
            y = r_.uniform(base + 80, H - 30)
            z.add(x, 30, lambda X, y=y, c=c: gumdrop(X, y, 22, c))
    return ground_base(yf, zone), "", z


# ======================================================================= assemble
def doc(body, uid=""):
    s = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">'
         f'<defs><clipPath id="frame"><rect width="{W}" height="{H}"/></clipPath></defs>'
         f'<g transform="translate(0 420)"><g clip-path="url(#frame)">{body}</g></g></svg>')
    return s


def zone1_layers():
    layers, spills = [], []
    for fn in (z1_sky, z1_mountains, z1_hills, z1_trees, z1_ground):
        REC.clear()
        body = fn()
        rec = list(REC)
        layers.append(body)
        spill = [(x - W, e, d) for x, e, d in rec if x + e > W] + [(x, e, d) for x, e, d in rec if x < e]
        spills.append(spill)
    return layers, spills


LAYER_NAMES = ["01_sky", "02_mountains", "03_hills", "04_trees", "05_ground"]
ZONE_DIRS = {1: "zone_01_meadow"}
ZONE_LABELS = {1: "Meadow"}
for n, c in ZONES.items():
    ZONE_DIRS[n] = f"zone_{n:02d}_{c['name']}"
    ZONE_LABELS[n] = c["label"]

all_full = {}
layers1, carry = zone1_layers()
zone_bodies = {1: layers1}
for n in range(2, N_ZONES + 1):
    cfg = ZONES[n]
    bodies, new_carry = [], []
    builders = (lambda: sky_layer(n), lambda: mountains_layer(n, cfg), lambda: hills_layer(n, cfg),
                lambda: trees_layer(n, cfg), lambda: ground_layer(n, cfg))
    for li, b in enumerate(builders):
        pre, post, z = b()
        bodies.append(pre + z.svg(carry[li]) + post)
        new_carry.append(z.spill())
    zone_bodies[n] = bodies
    carry = new_carry

for n, bodies in zone_bodies.items():
    d = os.path.join(OUT, ZONE_DIRS[n], "svg")
    os.makedirs(d, exist_ok=True)
    for name, body in zip(LAYER_NAMES, bodies):
        with open(os.path.join(d, f"layer_{name}.svg"), "w") as f:
            f.write(doc(body))
    full = "".join(bodies)
    all_full[n] = full
    with open(os.path.join(d, "background_full.svg"), "w") as f:
        f.write(doc(full))

# Preview: 2 rows x 3 zones, each row continuous (zone 3 -> 4 continues on the next row)
cells = []
for i, n in enumerate(range(1, N_ZONES + 1)):
    row, col = divmod(i, 5)
    body = all_full[n]
    for ident in ("skyc", "skyfade", "glow", "grd", "mb", "mf", "hl", "tr", "gd", "gs"):
        body = body.replace(f'id="{ident}"', f'id="{ident}{n}"').replace(f'url(#{ident})', f'url(#{ident}{n})')
    x, y = col * 384, 40 + row * 272
    cells.append(f'<g transform="translate({x} {y}) scale(0.2)"><clipPath id="c{n}"><rect width="{W}" height="{H}"/></clipPath>'
                 f'<g clip-path="url(#c{n})">{body}</g></g>'
                 f'<text x="{x+192}" y="{y+248}" text-anchor="middle" font-family="Arial Rounded MT Bold, Arial, sans-serif" '
                 f'font-size="20" font-weight="bold" fill="{INK}">{n}. {ZONE_LABELS[n]}</text>')
with open(os.path.join(OUT, "zones_preview.svg"), "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">'
            f'<rect width="{W}" height="{W}" fill="#fff8ec"/>' + "".join(cells) + "</svg>")
print("zones:", list(ZONE_DIRS.values()))
