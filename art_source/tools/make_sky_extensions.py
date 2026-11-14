"""Sky extensions: one 1920x1080 image to stack directly above each zone's sky.

* bottom edge = #5ec8ff, exactly the top color of every zone's sky layer -> invisible vertical seam
* top edge   = #3b9fe8 -> fill anything higher with that solid color
* extensions connect left->right in zone order (elements cut by a right edge continue on the next one)

Usage: python3 make_sky_extensions.py <golf_zones_dir>
Writes <zone>/svg/layer_00_sky_extension.svg (1920x1920 canvas, scene at rows 420..1500) and
<golf_zones_dir>/sky_preview.svg.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zone_palette import hgrad  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else "golf_zones"
W, H = 1920, 1080
INK = "#1d3a2a"
BOTTOM, TOP = "#5ec8ff", "#3b9fe8"
ZONES = ["zone_01_meadow", "zone_02_rocky_highlands", "zone_03_ancient_ruins",
         "zone_04_jungle_temple", "zone_05_mountain_shrine", "zone_06_mystic_stones",
         "zone_07_sunny_coast", "zone_08_windmill_farm", "zone_09_autumn_woods",
         "zone_10_volcano_ridge", "zone_11_sky_isles", "zone_12_royal_castle",
         "zone_13_frozen_peaks", "zone_14_desert_oasis", "zone_15_mushroom_grove", "zone_16_candy_land",
         "zone_17_starlight_summit", "zone_18_coral_lagoon", "zone_19_bamboo_forest", "zone_20_golden_savanna",
         "zone_21_lavender_fields", "zone_22_neon_city"]
LABELS = ["Meadow", "Rocky Highlands", "Ancient Ruins", "Jungle Temple", "Mountain Shrine", "Mystic Stones",
          "Sunny Coast", "Windmill Farm", "Autumn Woods", "Volcano Ridge", "Sky Isles", "Royal Castle",
          "Frozen Peaks", "Desert Oasis", "Mushroom Grove", "Candy Land", "Starlight Summit",
          "Coral Lagoon", "Bamboo Forest", "Golden Savanna", "Lavender Fields", "Neon City"]


def blob(circles, fill, stroke=INK, sw=5):
    out = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw*2}"/>'
                  for x, y, r in circles) if stroke else ""
    return out + "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>' for x, y, r in circles)


PARTS = [(0, 0, 46), (52, -18, 58), (110, 0, 44), (58, 14, 46), (-34, 12, 32), (144, 14, 30)]


def cloud(X, y, sc):
    return blob([(X + a * sc, y + b * sc, r * sc) for a, b, r in PARTS], "#ffffff", stroke="#a9dff5", sw=3)


def wisp(X, y, s):
    return (f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{s:.1f}" ry="{s*0.09:.1f}" fill="#ffffff" opacity="0.55"/>'
            f'<ellipse cx="{X+s*0.35:.1f}" cy="{y+s*0.12:.1f}" rx="{s*0.6:.1f}" ry="{s*0.07:.1f}" fill="#ffffff" opacity="0.45"/>')


def bird(X, y, s):
    return (f'<path d="M{X-s:.1f} {y:.1f} Q{X-s*0.5:.1f} {y-s*0.65:.1f} {X:.1f} {y:.1f} Q{X+s*0.5:.1f} {y-s*0.65:.1f} {X+s:.1f} {y:.1f}" '
            f'fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')


def flock(X, y, n, s, rnd):
    return "".join(bird(X + i * s * 2.4 + rnd.uniform(-8, 8), y + abs(i - n // 2) * s * 0.9 + rnd.uniform(-5, 5), s) for i in range(n))


def balloon(X, y, s, c1="#ff6b6b", c2="#ffe14d"):
    env = (f"M{X:.1f} {y+s*0.95:.1f} Q{X-s*0.95:.1f} {y+s*0.35:.1f} {X-s*0.85:.1f} {y-s*0.35:.1f} "
           f"Q{X-s*0.7:.1f} {y-s:.1f} {X:.1f} {y-s:.1f} Q{X+s*0.7:.1f} {y-s:.1f} {X+s*0.85:.1f} {y-s*0.35:.1f} "
           f"Q{X+s*0.95:.1f} {y+s*0.35:.1f} {X:.1f} {y+s*0.95:.1f} Z")
    return (f'<clipPath id="bc{int(X)}_{int(y)}"><path d="{env}"/></clipPath>'
            f'<path d="{env}" fill="{c1}"/>'
            f'<g clip-path="url(#bc{int(X)}_{int(y)})">'
            + "".join(f'<rect x="{X-s+i*s*0.5:.1f}" y="{y-s:.1f}" width="{s*0.25:.1f}" height="{s*2:.1f}" fill="{c2}"/>' for i in range(4))
            + '</g>'
            f'<path d="{env}" fill="none" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<line x1="{X-s*0.3:.1f}" y1="{y+s*0.85:.1f}" x2="{X-s*0.2:.1f}" y2="{y+s*1.25:.1f}" stroke="{INK}" stroke-width="3"/>'
            f'<line x1="{X+s*0.3:.1f}" y1="{y+s*0.85:.1f}" x2="{X+s*0.2:.1f}" y2="{y+s*1.25:.1f}" stroke="{INK}" stroke-width="3"/>'
            f'<rect x="{X-s*0.24:.1f}" y="{y+s*1.25:.1f}" width="{s*0.48:.1f}" height="{s*0.32:.1f}" rx="4" fill="#a8642e" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{X-s*0.55:.1f} {y-s*0.55:.1f} Q{X-s*0.45:.1f} {y-s*0.85:.1f} {X-s*0.15:.1f} {y-s*0.88:.1f}" fill="none" stroke="#ffffff" stroke-opacity="0.5" stroke-width="5" stroke-linecap="round"/>')


def eagle(X, y, s):
    return (f'<path d="M{X:.1f} {y:.1f} Q{X-s*0.5:.1f} {y-s*0.45:.1f} {X-s*1.2:.1f} {y-s*0.2:.1f} L{X-s*1.05:.1f} {y-s*0.05:.1f} '
            f'L{X-s*1.15:.1f} {y+s*0.05:.1f} Q{X-s*0.5:.1f} {y:.1f} {X-s*0.12:.1f} {y+s*0.18:.1f} L{X:.1f} {y+s*0.42:.1f} '
            f'L{X+s*0.12:.1f} {y+s*0.18:.1f} Q{X+s*0.5:.1f} {y:.1f} {X+s*1.15:.1f} {y+s*0.05:.1f} L{X+s*1.05:.1f} {y-s*0.05:.1f} '
            f'L{X+s*1.2:.1f} {y-s*0.2:.1f} Q{X+s*0.5:.1f} {y-s*0.45:.1f} {X:.1f} {y:.1f} Z" fill="#6b4423" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<circle cx="{X:.1f}" cy="{y-s*0.05:.1f}" r="{s*0.12:.1f}" fill="#f4f0e6" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M{X-s*0.03:.1f} {y+s*0.02:.1f} L{X:.1f} {y+s*0.1:.1f} L{X+s*0.03:.1f} {y+s*0.02:.1f}" fill="#f5b82e"/>')


def dove(X, y, s):
    return (f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{s*0.45:.1f}" ry="{s*0.2:.1f}" fill="#ffffff" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M{X-s*0.1:.1f} {y-s*0.05:.1f} Q{X-s*0.3:.1f} {y-s*0.75:.1f} {X+s*0.25:.1f} {y-s*0.6:.1f} Q{X+s*0.1:.1f} {y-s*0.3:.1f} {X+s*0.12:.1f} {y-s*0.05:.1f} Z" fill="#ffffff" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
            f'<circle cx="{X+s*0.45:.1f}" cy="{y-s*0.1:.1f}" r="{s*0.13:.1f}" fill="#ffffff" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M{X+s*0.57:.1f} {y-s*0.1:.1f} L{X+s*0.68:.1f} {y-s*0.06:.1f} L{X+s*0.57:.1f} {y-s*0.02:.1f} Z" fill="#f5b82e"/>')


def parrot(X, y, s, body="#ff4d5e", wing="#2c7be5", tail="#ffe14d"):
    return (f'<path d="M{X-s*0.4:.1f} {y+s*0.05:.1f} L{X-s*1.1:.1f} {y+s*0.35:.1f} L{X-s*0.95:.1f} {y+s*0.12:.1f} L{X-s*1.15:.1f} {y+s*0.05:.1f} Z" fill="{tail}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
            f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{s*0.5:.1f}" ry="{s*0.22:.1f}" fill="{body}" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M{X-s*0.15:.1f} {y-s*0.08:.1f} Q{X-s*0.05:.1f} {y-s*0.8:.1f} {X+s*0.35:.1f} {y-s*0.7:.1f} Q{X+s*0.2:.1f} {y-s*0.3:.1f} {X+s*0.15:.1f} {y-s*0.05:.1f} Z" fill="{wing}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
            f'<circle cx="{X+s*0.5:.1f}" cy="{y-s*0.08:.1f}" r="{s*0.16:.1f}" fill="{body}" stroke="{INK}" stroke-width="3"/>'
            f'<circle cx="{X+s*0.54:.1f}" cy="{y-s*0.12:.1f}" r="{s*0.04:.1f}" fill="{INK}"/>'
            f'<path d="M{X+s*0.64:.1f} {y-s*0.12:.1f} Q{X+s*0.8:.1f} {y-s*0.05:.1f} {X+s*0.64:.1f} {y+s*0.02:.1f} Z" fill="#f4f0e6" stroke="{INK}" stroke-width="2"/>')


def kite(X, y, s, c1, c2, rot):
    pts = f"{X:.1f},{y-s:.1f} {X+s*0.6:.1f},{y-s*0.2:.1f} {X:.1f},{y+s:.1f} {X-s*0.6:.1f},{y-s*0.2:.1f}"
    tail = f"M{X:.1f} {y+s:.1f} Q{X-s*0.4:.1f} {y+s*1.5:.1f} {X+s*0.1:.1f} {y+s*2:.1f} Q{X+s*0.5:.1f} {y+s*2.5:.1f} {X:.1f} {y+s*3:.1f}"
    bows = "".join(f'<path d="M{X+dx-10:.1f} {y+s*f-6:.1f} L{X+dx+10:.1f} {y+s*f+6:.1f} L{X+dx+10:.1f} {y+s*f-6:.1f} L{X+dx-10:.1f} {y+s*f+6:.1f} Z" fill="{c2}" stroke="{INK}" stroke-width="2"/>'
                   for f, dx in ((1.5, -s * 0.18), (2.0, s * 0.1), (2.5, s * 0.2)))
    return (f'<g transform="rotate({rot} {X:.1f} {y:.1f})">'
            f'<path d="{tail}" fill="none" stroke="{INK}" stroke-width="3"/>{bows}'
            f'<polygon points="{pts}" fill="{c1}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<polygon points="{X:.1f},{y-s:.1f} {X+s*0.6:.1f},{y-s*0.2:.1f} {X:.1f},{y-s*0.2:.1f}" fill="{c2}"/>'
            f'<polygon points="{X:.1f},{y-s*0.2:.1f} {X-s*0.6:.1f},{y-s*0.2:.1f} {X:.1f},{y+s:.1f}" fill="{c2}"/>'
            f'<polygon points="{pts}" fill="none" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
            f'<line x1="{X:.1f}" y1="{y-s:.1f}" x2="{X:.1f}" y2="{y+s:.1f}" stroke="{INK}" stroke-width="2"/>'
            f'<line x1="{X-s*0.6:.1f}" y1="{y-s*0.2:.1f}" x2="{X+s*0.6:.1f}" y2="{y-s*0.2:.1f}" stroke="{INK}" stroke-width="2"/></g>')


def crane(X, y, s):
    return (f'<path d="M{X-s*0.9:.1f} {y:.1f} L{X+s*0.9:.1f} {y-s*0.05:.1f}" stroke="{INK}" stroke-width="{s*0.12+4:.1f}" stroke-linecap="round"/>'
            f'<path d="M{X-s*0.9:.1f} {y:.1f} L{X+s*0.9:.1f} {y-s*0.05:.1f}" stroke="#ffffff" stroke-width="{s*0.12:.1f}" stroke-linecap="round"/>'
            f'<path d="M{X-s*0.1:.1f} {y:.1f} Q{X-s*0.5:.1f} {y-s*0.6:.1f} {X-s*1.0:.1f} {y-s*0.75:.1f} Q{X-s*0.4:.1f} {y-s*0.25:.1f} {X+s*0.2:.1f} {y:.1f} Z" fill="#ffffff" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
            f'<path d="M{X-s*1.0:.1f} {y-s*0.75:.1f} Q{X-s*0.85:.1f} {y-s*0.6:.1f} {X-s*0.72:.1f} {y-s*0.56:.1f}" fill="none" stroke="{INK}" stroke-width="5"/>'
            f'<circle cx="{X+s*0.95:.1f}" cy="{y-s*0.07:.1f}" r="{s*0.06:.1f}" fill="#e2483a"/>')


def float_island(X, y, s, rnd):
    out = (f'<path d="M{X-s:.1f} {y:.1f} Q{X-s*0.6:.1f} {y+s*0.5:.1f} {X-s*0.1:.1f} {y+s*1.1:.1f} Q{X+s*0.3:.1f} {y+s*0.6:.1f} {X+s:.1f} {y:.1f} Z" '
           f'fill="#a3aca2" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
           f'<path d="M{X-s*0.4:.1f} {y+s*0.25:.1f} L{X-s*0.2:.1f} {y+s*0.55:.1f}" stroke="#7f897f" stroke-width="3"/>'
           f'<path d="M{X-s*1.05:.1f} {y+2:.1f} Q{X:.1f} {y-s*0.22:.1f} {X+s*1.05:.1f} {y+2:.1f} Q{X:.1f} {y+s*0.12:.1f} {X-s*1.05:.1f} {y+2:.1f} Z" fill="#55c36b" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>')
    out += (f'<path d="M{X-s*0.15:.1f} {y-s*0.1:.1f} L{X-s*0.12:.1f} {y-s*0.75:.1f} Q{X:.1f} {y-s*0.85:.1f} {X+s*0.12:.1f} {y-s*0.75:.1f} L{X+s*0.15:.1f} {y-s*0.1:.1f} Z" fill="#a7b0bd" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{X:.1f} {y-s*0.6:.1f} L{X:.1f} {y-s*0.3:.1f} M{X-s*0.06:.1f} {y-s*0.5:.1f} L{X:.1f} {y-s*0.6:.1f} L{X+s*0.06:.1f} {y-s*0.5:.1f}" stroke="#7ef0ff" stroke-width="3" fill="none" stroke-linecap="round"/>')
    return out


def float_crystal(X, y, s, c, c2):
    return (f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{s*1.3:.1f}" fill="{c}" opacity="0.18"/>'
            f'<polygon points="{X:.1f},{y-s:.1f} {X+s*0.45:.1f},{y:.1f} {X:.1f},{y+s:.1f} {X-s*0.45:.1f},{y:.1f}" fill="{c}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<polygon points="{X:.1f},{y-s:.1f} {X+s*0.45:.1f},{y:.1f} {X:.1f},{y:.1f}" fill="{c2}" opacity="0.7"/>')


def sparkle(X, y, s, c="#ffffff"):
    return (f'<path d="M{X:.1f} {y-s:.1f} Q{X+s*0.15:.1f} {y-s*0.15:.1f} {X+s:.1f} {y:.1f} Q{X+s*0.15:.1f} {y+s*0.15:.1f} {X:.1f} {y+s:.1f} '
            f'Q{X-s*0.15:.1f} {y+s*0.15:.1f} {X-s:.1f} {y:.1f} Q{X-s*0.15:.1f} {y-s*0.15:.1f} {X:.1f} {y-s:.1f} Z" fill="{c}" opacity="0.9"/>')


def aurora():
    out = ""
    for i, (c, base, amp, k, op) in enumerate((("#7ef0ff", 150, 40, 3, 0.25), ("#9bffb0", 210, 35, 2, 0.22), ("#c9a6ff", 120, 30, 4, 0.18))):
        top = [(x, base + amp * math.sin(2 * math.pi * k * x / W + i)) for x in range(0, W + 32, 32)]
        d = "M" + " L".join(f"{x} {y:.1f}" for x, y in top) + " " + " ".join(f"L{x} {y+70:.1f}" for x, y in reversed(top)) + " Z"
        out += f'<path d="{d}" fill="{c}" opacity="{op}"/>'
    # fade both ends so the aurora never starts with a hard edge at a zone seam
    return ('<defs><linearGradient id="afade" x1="0" y1="0" x2="1" y2="0">'
            '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.3" stop-color="#fff" stop-opacity="1"/>'
            '<stop offset="0.75" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="amask"><rect width="{W}" height="{H}" fill="url(#afade)"/></mask></defs>'
            f'<g mask="url(#amask)">{out}</g>')


def falling_leaf(X, y, s, rot, c):
    return (f'<g transform="rotate({rot} {X:.1f} {y:.1f})"><path d="M{X-s:.1f} {y:.1f} Q{X:.1f} {y-s*0.8:.1f} {X+s:.1f} {y:.1f} Q{X:.1f} {y+s*0.8:.1f} {X-s:.1f} {y:.1f} Z" '
            f'fill="{c}" stroke="{INK}" stroke-width="3"/><line x1="{X-s:.1f}" y1="{y:.1f}" x2="{X+s*0.8:.1f}" y2="{y:.1f}" stroke="{INK}" stroke-width="2"/></g>')


def firework(X, y, r, c):
    out = ""
    for k in range(12):
        a = math.radians(k * 30)
        out += (f'<line x1="{X + math.cos(a)*r*0.35:.1f}" y1="{y + math.sin(a)*r*0.35:.1f}" x2="{X + math.cos(a)*r:.1f}" y2="{y + math.sin(a)*r:.1f}" '
                f'stroke="{c}" stroke-width="7" stroke-linecap="round"/>'
                f'<circle cx="{X + math.cos(a)*r*1.12:.1f}" cy="{y + math.sin(a)*r*1.12:.1f}" r="5" fill="{c}"/>')
    return out + f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r*0.14:.1f}" fill="#ffffff"/>'


def ash_cloud(X, y, sc):
    return blob([(X + a * sc, y + b * sc, r * sc) for a, b, r in PARTS], "#c9ccc6", stroke="#9aa09a", sw=3)


# ---------------------------------------------------------------------- per-zone content
def build(zi, rnd):
    els = []   # (x, ext, draw)

    def add(x, ext, draw):
        els.append((x, ext, draw))

    # shared: puffy clouds lower down, wispy clouds high up
    for i in range(0 if zi in (16, 21) else 3):
        x, y, sc = i * W / 3 + rnd.uniform(60, 400), rnd.uniform(520, 900), rnd.uniform(0.8, 1.2)
        if zi == 15:
            add(x, 182 * sc, lambda X, y=y, sc=sc: blob([(X + a * sc, y + b * sc, r * sc) for a, b, r in PARTS], "#ffe3f1", stroke="#f7b6d6", sw=3))
        else:
            add(x, 182 * sc, lambda X, y=y, sc=sc: cloud(X, y, sc))
    for i in range(0 if zi in (16, 21) else 3):
        x, y, s = i * W / 3 + rnd.uniform(80, 400), rnd.uniform(120, 420), rnd.uniform(160, 240)
        add(x, s * 1.3, lambda X, y=y, s=s: wisp(X, y, s))

    if zi == 0:
        add(1350, 80, lambda X: balloon(X, 380, 70))
        add(420, 70, lambda X: balloon(X, 700, 45, "#2c7be5", "#ffffff"))
        for x, y in ((700, 300), (1650, 620)):
            add(x, 80, lambda X, y=y: flock(X, y, 4, 16, random.Random(int(X))))
    elif zi == 1:
        for x, y, s in ((600, 350, 60), (1450, 520, 48), (1000, 200, 36)):
            add(x, s * 1.25, lambda X, y=y, s=s: eagle(X, y, s))
        add(250, 80, lambda X: flock(X, 760, 3, 14, random.Random(5)))
    elif zi == 2:
        for x, y, s in ((380, 420, 60), (520, 470, 50), (1250, 300, 64), (1380, 360, 52), (1700, 650, 46)):
            add(x, s * 0.8, lambda X, y=y, s=s: dove(X, y, s))
        add(900, 80, lambda X: balloon(X, 560, 55, "#e3d9bf", "#c4b796"))
    elif zi == 3:
        for x, y, s, cols in ((450, 380, 70, ("#ff4d5e", "#2c7be5", "#ffe14d")), (980, 560, 60, ("#2c7be5", "#ffe14d", "#ff4d5e")),
                              (1500, 300, 66, ("#3fb45a", "#ff4d5e", "#ffe14d")), (1750, 700, 50, ("#ffb02e", "#2c7be5", "#3fb45a"))):
            add(x, s * 1.2, lambda X, y=y, s=s, cols=cols: parrot(X, y, s, *cols))
    elif zi == 4:
        for x, y, s, c1, c2, r in ((400, 420, 60, "#e2483a", "#ffe14d", -10), (1050, 260, 52, "#2c7be5", "#ffffff", 8),
                                   (1600, 520, 58, "#ff8fc7", "#ffffff", -6)):
            add(x, s * 0.8, lambda X, y=y, s=s, c1=c1, c2=c2, r=r: kite(X, y, s, c1, c2, r))
        for x, y in ((700, 640), (790, 600), (1300, 720)):
            add(x, 70, lambda X, y=y: crane(X, y, 60))
    elif zi == 5:
        for x, y, s in ((500, 520, 110), (1300, 330, 140), (1750, 680, 80)):
            add(x, s * 1.1, lambda X, y=y, s=s: float_island(X, y, s, rnd))
        for x, y, c, c2 in ((850, 420, "#b98cff", "#e2ccff"), (1000, 700, "#6fe3ff", "#d2f8ff"), (220, 300, "#6fe3ff", "#d2f8ff")):
            add(x, 40, lambda X, y=y, c=c, c2=c2: float_crystal(X, y, 28, c, c2))
        for _ in range(9):
            x, y = rnd.uniform(40, W - 40), rnd.uniform(80, 900)
            add(x, 14, lambda X, y=y: sparkle(X, y, rnd.uniform(6, 12)))
    elif zi == 6:
        for x, y in ((420, 420), (1300, 300), (1700, 620)):
            add(x, 80, lambda X, y=y: flock(X, y, 3, 18, random.Random(int(X) + 7)))
        for x, y, s_, c1, c2, r in ((800, 380, 56, "#4cc3f0", "#ffffff", -8), (1550, 220, 50, "#ffb02e", "#ff6b6b", 10)):
            add(x, s_ * 0.8, lambda X, y=y, s_=s_, c1=c1, c2=c2, r=r: kite(X, y, s_, c1, c2, r))
    elif zi == 7:
        add(600, 80, lambda X: balloon(X, 400, 62, "#3fb45a", "#ffe14d"))
        add(1450, 80, lambda X: balloon(X, 620, 48, "#ff8fc7", "#ffffff"))
        add(1050, 80, lambda X: flock(X, 260, 4, 15, random.Random(9)))
    elif zi == 8:
        for _ in range(14):
            x, y = rnd.uniform(60, W - 60), rnd.uniform(100, 950)
            c = rnd.choice(["#e8913a", "#d9673a", "#f2b33d"])
            add(x, 20, lambda X, y=y, c=c, rot=int(rnd.uniform(0, 180)): falling_leaf(X, y, 14, rot, c))
        add(900, 80, lambda X: flock(X, 330, 3, 16, random.Random(11)))
    elif zi == 9:
        for x, y, sc in ((500, 300, 1.1), (1250, 450, 1.3), (1700, 220, 0.9)):
            add(x, 182 * sc, lambda X, y=y, sc=sc: ash_cloud(X, y, sc))
        for x, y, s in ((850, 560, 54), (1500, 700, 42)):
            add(x, s * 1.25, lambda X, y=y, s=s: eagle(X, y, s))
    elif zi == 10:
        for x, y, s in ((450, 560, 100), (1250, 320, 130), (1720, 700, 80)):
            add(x, s * 1.1, lambda X, y=y, s=s: float_island(X, y, s, rnd))
        for _ in range(8):
            x, y = rnd.uniform(40, W - 40), rnd.uniform(80, 900)
            add(x, 14, lambda X, y=y: sparkle(X, y, rnd.uniform(6, 12)))
    elif zi == 11:
        for x, y, r, c in ((400, 330, 70, "#ff6b6b"), (820, 200, 90, "#ffe14d"), (1250, 380, 80, "#7ef0ff"),
                           (1650, 240, 75, "#c9a6ff"), (1050, 620, 55, "#ff8fc7")):
            add(x, r * 1.2, lambda X, y=y, r=r, c=c: firework(X, y, r, c))
    elif zi == 12:      # Frozen Peaks: snowflakes + birds
        for _ in range(26):
            x, y = rnd.uniform(30, W - 30), rnd.uniform(60, 1000)
            add(x, 12, lambda X, y=y, r=rnd.uniform(4, 9): snowflake(X, y, r))
        add(1200, 80, lambda X: flock(X, 300, 3, 15, random.Random(21)))
    elif zi == 13:      # Desert Oasis: vultures circling, heat-haze sun
        add(1500, 160, lambda X: f'<circle cx="{X}" cy="420" r="150" fill="#fff1c4" opacity="0.35"/><circle cx="{X}" cy="420" r="70" fill="#ffe08a" stroke="#f5b82e" stroke-width="7"/>')
        for x, y, s in ((600, 380, 44), (820, 300, 38)):
            add(x, s * 1.25, lambda X, y=y, s=s: eagle(X, y, s))
    elif zi == 14:      # Mushroom Grove: floating glowing spores
        for _ in range(18):
            x, y = rnd.uniform(40, W - 40), rnd.uniform(80, 980)
            c = rnd.choice(["#7ef0ff", "#c9a6ff", "#fff38a", "#ff8fc7"])
            add(x, 16, lambda X, y=y, c=c, r=rnd.uniform(4, 8): f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r*2.4:.1f}" fill="{c}" opacity="0.22"/><circle cx="{X:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}"/>')
    elif zi == 15:      # Candy Land: balloons + sprinkles
        add(500, 80, lambda X: balloon(X, 420, 58, "#ff8fc7", "#ffffff"))
        add(1400, 80, lambda X: balloon(X, 300, 48, "#7ef0c0", "#ffe14d"))
        for _ in range(16):
            x, y = rnd.uniform(40, W - 40), rnd.uniform(80, 980)
            c = rnd.choice(["#ff6b6b", "#ffe14d", "#4cc3f0", "#7ef0c0", "#c9a6ff"])
            add(x, 10, lambda X, y=y, c=c, rot=int(rnd.uniform(0, 180)): f'<rect x="{X-7:.1f}" y="{y-2.5:.1f}" width="14" height="5" rx="2.5" transform="rotate({rot} {X:.1f} {y:.1f})" fill="{c}"/>')
    elif zi == 16:      # Starlight Summit: stars, shooting star, aurora
        for _ in range(70):
            x, y = rnd.uniform(10, W - 10), rnd.uniform(10, 1060)
            add(x, 8, lambda X, y=y, r=rnd.uniform(1.5, 3.5): f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#fff7c2"/>')
        for x, y in ((520, 300), (1420, 640), (980, 160)):
            add(x, 16, lambda X, y=y: sparkle(X, y, 12, "#fff7c2"))
        add(1200, 220, lambda X: f'<path d="M{X-200} 360 L{X} 300" stroke="#ffffff" stroke-width="5" stroke-linecap="round" opacity="0.8"/><circle cx="{X}" cy="300" r="7" fill="#ffffff"/>')
    elif zi == 17:      # Coral Lagoon: seagulls + kites
        for x, y in ((380, 360), (1250, 280), (1700, 640)):
            add(x, 80, lambda X, y=y: flock(X, y, 3, 18, random.Random(int(X) + 31)))
        add(860, 60, lambda X: kite(X, 420, 54, "#ff6b8a", "#ffffff", -10))
    elif zi == 18:      # Bamboo Forest: drifting green leaves + cranes
        for _ in range(14):
            x, y = rnd.uniform(60, W - 60), rnd.uniform(100, 950)
            c = rnd.choice(["#5cb85c", "#7cc96a", "#a8d86a"])
            add(x, 20, lambda X, y=y, c=c, rot=int(rnd.uniform(0, 180)): falling_leaf(X, y, 14, rot, c))
        for x, y in ((700, 620), (790, 590)):
            add(x, 70, lambda X, y=y: crane(X, y, 58))
    elif zi == 19:      # Golden Savanna: big flock in the sunset
        for x, y in ((500, 400), (1300, 300)):
            add(x, 120, lambda X, y=y: flock(X, y, 5, 16, random.Random(int(X) + 41)))
        add(1000, 80, lambda X: balloon(X, 620, 52, "#ff9f43", "#ffe14d"))
    elif zi == 20:      # Lavender Fields: butterflies
        for _ in range(12):
            x, y = rnd.uniform(60, W - 60), rnd.uniform(200, 980)
            c = rnd.choice(["#ffffff", "#ffe14d", "#ff8fc7", "#a77fe0"])
            add(x, 20, lambda X, y=y, c=c: butterfly(X, y, 14, c))
    elif zi == 21:      # Neon City: stars + blimp with lights
        for _ in range(60):
            x, y = rnd.uniform(10, W - 10), rnd.uniform(10, 1060)
            add(x, 8, lambda X, y=y, r=rnd.uniform(1.5, 3.2): f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="#fff7c2"/>')
        add(1100, 200, lambda X: blimp(X, 520, 160))
        for x, y, r, c in ((420, 300, 60, "#ff4fd8"), (1650, 250, 70, "#4ff0ff")):
            add(x, r * 1.2, lambda X, y=y, r=r, c=c: firework(X, y, r, c))
    return els


def butterfly(X, y, s, c):
    return (f'<ellipse cx="{X-s*0.5:.1f}" cy="{y-s*0.3:.1f}" rx="{s*0.55:.1f}" ry="{s*0.45:.1f}" fill="{c}" stroke="{INK}" stroke-width="2.5"/>'
            f'<ellipse cx="{X+s*0.5:.1f}" cy="{y-s*0.3:.1f}" rx="{s*0.55:.1f}" ry="{s*0.45:.1f}" fill="{c}" stroke="{INK}" stroke-width="2.5"/>'
            f'<ellipse cx="{X-s*0.35:.1f}" cy="{y+s*0.3:.1f}" rx="{s*0.35:.1f}" ry="{s*0.3:.1f}" fill="{c}" stroke="{INK}" stroke-width="2.5"/>'
            f'<ellipse cx="{X+s*0.35:.1f}" cy="{y+s*0.3:.1f}" rx="{s*0.35:.1f}" ry="{s*0.3:.1f}" fill="{c}" stroke="{INK}" stroke-width="2.5"/>'
            f'<line x1="{X:.1f}" y1="{y-s*0.6:.1f}" x2="{X:.1f}" y2="{y+s*0.6:.1f}" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')


def blimp(X, y, w):
    h = w * 0.36
    return (f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{w/2:.1f}" ry="{h/2:.1f}" fill="#d9d4e8" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{X+w*0.42:.1f} {y:.1f} L{X+w*0.62:.1f} {y-h*0.45:.1f} L{X+w*0.62:.1f} {y+h*0.45:.1f} Z" fill="#b9b3d9" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<rect x="{X-w*0.12:.1f}" y="{y+h*0.45:.1f}" width="{w*0.24:.1f}" height="{h*0.25:.1f}" rx="5" fill="#8f89c0" stroke="{INK}" stroke-width="3"/>'
            + "".join(f'<circle cx="{X - w*0.35 + i*w*0.14:.1f}" cy="{y:.1f}" r="5" fill="{c}"/>' for i, c in enumerate(["#ff4fd8", "#4ff0ff", "#ffe14d", "#ff4fd8", "#4ff0ff", "#ffe14d"])))


def snowflake(X, y, r):
    out = ""
    for k in range(3):
        a = math.radians(k * 60)
        out += f'<line x1="{X - math.cos(a)*r:.1f}" y1="{y - math.sin(a)*r:.1f}" x2="{X + math.cos(a)*r:.1f}" y2="{y + math.sin(a)*r:.1f}" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/>'
    return out


def doc(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">'
            f'<defs><clipPath id="frame"><rect width="{W}" height="{H}"/></clipPath>'
            f'<linearGradient id="hsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TOP}"/>'
            f'<stop offset="1" stop-color="{BOTTOM}"/></linearGradient></defs>'
            f'<g transform="translate(0 420)"><g clip-path="url(#frame)">{body}</g></g></svg>')


bodies, carry = [], []
for zi, zone in enumerate(ZONES):
    rnd = random.Random(900 + zi)
    els = build(zi, rnd)
    z1 = zi + 1
    body = ('<defs>' + hgrad("exb", z1, "sky") + hgrad("exh", z1, "high") +
            '<linearGradient id="exv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/>'
            '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>'
            f'<mask id="exm"><rect width="{W}" height="{H}" fill="url(#exv)"/></mask></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#exb)"/>'
            f'<rect width="{W}" height="{H}" fill="url(#exh)" mask="url(#exm)"/>')
    if zi in (5, 16):
        body += aurora()
    body += "".join(d(x) for x, e, d in carry) + "".join(d(x) for x, e, d in els)
    carry = [(x - W, e, d) for x, e, d in els if x + e > W]
    bodies.append(body)
    out = os.path.join(ROOT, zone, "svg", "layer_00_sky_extension.svg")
    with open(out, "w") as f:
        f.write(doc(body))

# Preview: each column = sky extension stacked on its zone's full background
cells = []
for i, zone in enumerate(ZONES):
    row, col = divmod(i, 6)
    x = col * 320
    y0 = 60 + row * 430
    ext = bodies[i].replace('id="bc', f'id="p{i}bc').replace('url(#bc', f'url(#p{i}bc')
    for ident in ("exb", "exh", "exv", "exm", "afade", "amask"):
        ext = ext.replace(f'id="{ident}"', f'id="{ident}{i}"').replace(f'url(#{ident})', f'url(#{ident}{i})')
    full = open(os.path.join(ROOT, zone, "svg", "background_full.svg")).read()
    full = full.split('<g clip-path="url(#frame)">', 1)[1].rsplit("</g></g></svg>", 1)[0]
    for ident in ("skyc", "skyfade", "glow", "grd", "mb", "mf", "hl", "tr", "gd", "gs"):
        full = full.replace(f'id="{ident}"', f'id="{ident}{i}"').replace(f'url(#{ident})', f'url(#{ident}{i})')
    s = 320 / W
    cells.append(f'<g transform="translate({x} {y0}) scale({s})"><clipPath id="pc{i}"><rect width="{W}" height="{H*2}"/></clipPath>'
                 f'<g clip-path="url(#pc{i})"><rect width="{W}" height="{H}" fill="url(#hsky)"/>{ext}<g transform="translate(0 {H})">{full}</g></g></g>'
                 f'<text x="{x+160}" y="{y0 + 2*H*s + 34:.0f}" text-anchor="middle" font-family="Arial Rounded MT Bold, Arial, sans-serif" '
                 f'font-size="22" font-weight="bold" fill="{INK}">{i+1}. {LABELS[i]}</text>')
with open(os.path.join(ROOT, "sky_preview.svg"), "w") as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">'
            f'<defs><linearGradient id="hsky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{TOP}"/>'
            f'<stop offset="1" stop-color="{BOTTOM}"/></linearGradient></defs>'
            f'<rect width="{W}" height="{W}" fill="#fff8ec"/>' + "".join(cells) + "</svg>")
print("ok")
