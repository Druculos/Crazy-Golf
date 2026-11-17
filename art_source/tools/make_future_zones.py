"""Future World: 20 connected futuristic stages for the rebirth world.

Reuses the drawing helpers and terrain of make_golf_zones.py (same ground curve, so the game's physics stay the same),
with its own palette, a neon grid floor and new futuristic landmarks.

Usage: python3 make_future_zones.py <out_dir>
Writes <out>/fzone_NN_<name>/svg/{layer_00_sky_extension..layer_05_ground,background_full}.svg
(1920x1920 canvas, scene at rows 420..1500 — crop after rendering) and <out>/future_preview.svg.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_golf_zones as g  # noqa: E402
from make_golf_zones import (W, H, INK, blob, gpath, gridge, make_yf, wave, Z, place,  # noqa: E402
                             T_MTN_BACK, T_MTN_FRONT, T_HILLS, T_TREES, T_GROUND, CLOUD_PARTS,
                             round_tree, crystals, skyscraper, neon_sign, glow_lamp, giant_mushroom,
                             far_peak, far_mesa, moon, firefly, glow_flower, observatory, bush)

OUT = sys.argv[1] if len(sys.argv) > 1 else "future_zones"

STAGES = [
    ("neon_launchpad", "Neon Launchpad"), ("hover_highway", "Hover Highway"), ("robot_factory", "Robot Factory"),
    ("solar_fields", "Solar Fields"), ("cyber_garden", "Cyber Garden"), ("hologram_plaza", "Hologram Plaza"),
    ("maglev_station", "Maglev Station"), ("bio_dome", "Bio-Dome"), ("data_valley", "Data Valley"),
    ("quantum_lab", "Quantum Lab"), ("mech_yard", "Mech Yard"), ("sky_arcology", "Sky Arcology"),
    ("satellite_array", "Satellite Array"), ("space_port", "Space Port"), ("moon_base", "Moon Base"),
    ("asteroid_field", "Asteroid Field"), ("orbital_ring", "Orbital Ring"), ("nebula_gardens", "Nebula Gardens"),
    ("time_rift", "Time Rift"), ("star_gate", "Star Gate"),
]
N = len(STAGES)
NIGHT = {9, 13, 14, 15, 16, 17, 18, 19}

# sky, high, far mountains, near mountains, hills, trees band, ground, grid lines
FP = {
    1: ("#7fdcff", "#3aa7e6", "#c4ecff", "#9fd8f2", "#6ad1c8", "#4fb8b0", "#5fd6b8", "#9ff0dc"),
    2: ("#8ab8ff", "#4f7fe6", "#cfe0ff", "#a9c4f5", "#78b0e6", "#5f98d6", "#6fc8d6", "#a6e8f0"),
    3: ("#ffc48a", "#e88a4f", "#ead2b8", "#d4b494", "#b8a490", "#9c8a78", "#a8b0a0", "#e8a070"),
    4: ("#ffe08a", "#f0b84a", "#f5e8b8", "#e8d494", "#a8d86a", "#8fc95a", "#9fdc7a", "#fff3a8"),
    5: ("#8af0c0", "#3fc490", "#c8f8e0", "#a0ecc8", "#4fd88a", "#3fc078", "#5fe090", "#c8ffe0"),
    6: ("#c8a8ff", "#8a6ae6", "#e2d4ff", "#c8b4f5", "#9f8ae0", "#8572d0", "#8fa8e0", "#ff9ef0"),
    7: ("#6fe0e8", "#2fb0c4", "#bff2f5", "#94e2ea", "#58c4c8", "#44aab4", "#5fcab8", "#c8fff8"),
    8: ("#c8f08a", "#8fcc4a", "#e4f8c4", "#cdeca2", "#8fd65a", "#74c44a", "#8ee06a", "#eaffc8"),
    9: ("#1f4a3a", "#0c2a20", "#2f6a52", "#245a44", "#1f7a52", "#186a46", "#2a8a5a", "#5fff9f"),
    10: ("#9a7ae8", "#5f44b8", "#c4b4f2", "#a894e6", "#7a6ad0", "#6658bc", "#6a8ac8", "#9ef4ff"),
    11: ("#e8a070", "#c46a3a", "#e0c0a4", "#c8a284", "#a08a74", "#887464", "#96a088", "#ffc48a"),
    12: ("#b8e8ff", "#7cc4f0", "#f0faff", "#d8f0fc", "#9fd8e8", "#84c8dc", "#8fe0c8", "#ffffff"),
    13: ("#3a5aa8", "#1c2e6a", "#5a78c0", "#4a68b0", "#3f6a8a", "#345a78", "#3f7a74", "#7ef0ff"),
    14: ("#2a3a7a", "#10183f", "#46589a", "#3a4a88", "#34507a", "#2a4268", "#3a6670", "#ffb84f"),
    15: ("#20264a", "#0a0d24", "#3a4068", "#2e3458", "#8a8fa0", "#767b8c", "#a4a8b4", "#dfe6ff"),
    16: ("#1a1f3f", "#070a1f", "#343a64", "#2a3056", "#6a5a74", "#58485f", "#7a6e84", "#c9a6ff"),
    17: ("#2a2f6f", "#12154a", "#4a50a0", "#3c428a", "#3a6a9a", "#305a88", "#3a8a9a", "#7ef0ff"),
    18: ("#6a2f7f", "#3a1450", "#9a5ab0", "#8448a0", "#5a8a7a", "#4a786a", "#5aa080", "#ff9ef0"),
    19: ("#3a2a8a", "#1a0f50", "#6a5ac0", "#5848a8", "#4a5a9a", "#3c4c88", "#4a7a9a", "#c9a6ff"),
    20: ("#ffcf7a", "#e89a3a", "#ffe4b0", "#f5cc88", "#c8a0e8", "#b088d8", "#b8a0f0", "#ffffff"),
}
KEYS = {"sky": 0, "high": 1, "mb": 2, "mf": 3, "hills": 4, "trees": 5, "ground": 6, "grid": 7}


def mix(a, b, t=0.5):
    ra = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    rb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(ra[i] + (rb[i] - ra[i]) * t) for i in range(3))


def hgrad(gid, zone, key):
    k = KEYS[key]
    own = FP[zone][k]
    left = mix(FP[zone - 1][k], own) if zone > 1 else own
    right = mix(own, FP[zone + 1][k]) if zone < N else own
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="0">'
            f'<stop offset="0" stop-color="{left}"/><stop offset="0.3" stop-color="{own}"/>'
            f'<stop offset="0.7" stop-color="{own}"/><stop offset="1" stop-color="{right}"/></linearGradient>')


def layer_defs(zone, *pairs):
    return "<defs>" + "".join(hgrad(gid, zone, key) for gid, key in pairs) + "</defs>"


def sky_defs(zone):
    return ('<defs>' + hgrad("skyc", zone, "sky") +
            '<linearGradient id="skyfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#ffffff" stop-opacity="{0.25 if zone in NIGHT else 0.6}"/></linearGradient></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#skyc)"/><rect width="{W}" height="{H}" fill="url(#skyfade)"/>')


# ======================================================================= futuristic drawings
def glow(X, y, r, c, op=0.25):
    return f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}" opacity="{op}"/>'


def star_dot(X, y, r, c="#fff7c2"):
    return f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}"/>'


def pylon(X, y, h, c="#7ef0ff"):
    return (f'<path d="M{X-h*0.08:.1f} {y:.1f} L{X-h*0.02:.1f} {y-h:.1f} L{X+h*0.02:.1f} {y-h:.1f} L{X+h*0.08:.1f} {y:.1f} Z" fill="#c9d3e6" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            + "".join(f'<rect x="{X-h*(0.07-0.05*t):.1f}" y="{y-h*t-4:.1f}" width="{h*(0.14-0.1*t):.1f}" height="6" fill="{c}"/>' for t in (0.25, 0.5, 0.75))
            + glow(X, y - h, h * 0.12, c, 0.3) + f'<circle cx="{X:.1f}" cy="{y-h:.1f}" r="{h*0.035:.1f}" fill="{c}" stroke="{INK}" stroke-width="3"/>')


def hover_car(X, y, s, c):
    return (f'<ellipse cx="{X:.1f}" cy="{y+s*0.32:.1f}" rx="{s*0.7:.1f}" ry="{s*0.08:.1f}" fill="#7ef0ff" opacity="0.5"/>'
            f'<path d="M{X-s:.1f} {y:.1f} Q{X-s:.1f} {y-s*0.3:.1f} {X-s*0.5:.1f} {y-s*0.32:.1f} L{X+s*0.6:.1f} {y-s*0.3:.1f} Q{X+s*1.05:.1f} {y-s*0.22:.1f} {X+s:.1f} {y+s*0.05:.1f} '
            f'Q{X+s*0.6:.1f} {y+s*0.22:.1f} {X-s*0.6:.1f} {y+s*0.2:.1f} Q{X-s:.1f} {y+s*0.18:.1f} {X-s:.1f} {y:.1f} Z" fill="{c}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<path d="M{X-s*0.45:.1f} {y-s*0.3:.1f} Q{X-s*0.3:.1f} {y-s*0.7:.1f} {X+s*0.15:.1f} {y-s*0.68:.1f} Q{X+s*0.45:.1f} {y-s*0.62:.1f} {X+s*0.55:.1f} {y-s*0.3:.1f} Z" fill="#bff6ff" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<line x1="{X-s*0.85:.1f}" y1="{y+s*0.02:.1f}" x2="{X+s*0.85:.1f}" y2="{y+s*0.02:.1f}" stroke="#ffffff" stroke-width="3" opacity="0.6"/>')


def drone(X, y, s):
    return (f'<rect x="{X-s*0.35:.1f}" y="{y-s*0.15:.1f}" width="{s*0.7:.1f}" height="{s*0.3:.1f}" rx="{s*0.12:.1f}" fill="#d9e2f2" stroke="{INK}" stroke-width="3"/>'
            f'<line x1="{X-s:.1f}" y1="{y-s*0.25:.1f}" x2="{X+s:.1f}" y2="{y-s*0.25:.1f}" stroke="{INK}" stroke-width="3"/>'
            f'<ellipse cx="{X-s:.1f}" cy="{y-s*0.3:.1f}" rx="{s*0.35:.1f}" ry="{s*0.07:.1f}" fill="#9fb0c8"/><ellipse cx="{X+s:.1f}" cy="{y-s*0.3:.1f}" rx="{s*0.35:.1f}" ry="{s*0.07:.1f}" fill="#9fb0c8"/>'
            f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{s*0.08:.1f}" fill="#ff4fd8"/>')


def robot(X, y, s, c="#c9d3e6"):
    return (f'<rect x="{X-s*0.22:.1f}" y="{y-s*0.3:.1f}" width="{s*0.12:.1f}" height="{s*0.3:.1f}" fill="#8a94a8" stroke="{INK}" stroke-width="3"/>'
            f'<rect x="{X+s*0.1:.1f}" y="{y-s*0.3:.1f}" width="{s*0.12:.1f}" height="{s*0.3:.1f}" fill="#8a94a8" stroke="{INK}" stroke-width="3"/>'
            f'<rect x="{X-s*0.35:.1f}" y="{y-s*0.75:.1f}" width="{s*0.7:.1f}" height="{s*0.48:.1f}" rx="{s*0.08:.1f}" fill="{c}" stroke="{INK}" stroke-width="4"/>'
            f'<circle cx="{X:.1f}" cy="{y-s*0.52:.1f}" r="{s*0.09:.1f}" fill="#7ef0ff" stroke="{INK}" stroke-width="2"/>'
            f'<rect x="{X-s*0.26:.1f}" y="{y-s*1.08:.1f}" width="{s*0.52:.1f}" height="{s*0.3:.1f}" rx="{s*0.1:.1f}" fill="{c}" stroke="{INK}" stroke-width="4"/>'
            f'<rect x="{X-s*0.18:.1f}" y="{y-s*1.0:.1f}" width="{s*0.36:.1f}" height="{s*0.1:.1f}" rx="{s*0.05:.1f}" fill="#1d1236"/>'
            f'<circle cx="{X-s*0.08:.1f}" cy="{y-s*0.95:.1f}" r="{s*0.03:.1f}" fill="#7ef0ff"/><circle cx="{X+s*0.08:.1f}" cy="{y-s*0.95:.1f}" r="{s*0.03:.1f}" fill="#7ef0ff"/>'
            f'<line x1="{X:.1f}" y1="{y-s*1.08:.1f}" x2="{X:.1f}" y2="{y-s*1.25:.1f}" stroke="{INK}" stroke-width="3"/><circle cx="{X:.1f}" cy="{y-s*1.27:.1f}" r="{s*0.04:.1f}" fill="#ff4fd8"/>'
            f'<path d="M{X-s*0.35:.1f} {y-s*0.65:.1f} L{X-s*0.55:.1f} {y-s*0.4:.1f} M{X+s*0.35:.1f} {y-s*0.65:.1f} L{X+s*0.55:.1f} {y-s*0.85:.1f}" stroke="#8a94a8" stroke-width="{s*0.08:.1f}" stroke-linecap="round"/>')


def factory(X, y, w):
    h = w * 0.55
    s = f'<rect x="{X-w/2:.1f}" y="{y-h*0.6:.1f}" width="{w:.1f}" height="{h*0.6:.1f}" fill="#b8bfcc" stroke="{INK}" stroke-width="5"/>'
    for i in range(4):
        x0 = X - w / 2 + i * w / 4
        s += f'<path d="M{x0:.1f} {y-h*0.6:.1f} L{x0+w/4:.1f} {y-h*0.85:.1f} L{x0+w/4:.1f} {y-h*0.6:.1f} Z" fill="#9aa3b4" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
        s += f'<rect x="{x0+w*0.04:.1f}" y="{y-h*0.42:.1f}" width="{w*0.15:.1f}" height="{h*0.12:.1f}" fill="#ffd36b" stroke="{INK}" stroke-width="3"/>'
    for cx in (X + w * 0.3, X + w * 0.42):
        s += f'<rect x="{cx-12:.1f}" y="{y-h*1.25:.1f}" width="24" height="{h*0.65:.1f}" fill="#8a94a8" stroke="{INK}" stroke-width="4"/>'
        s += blob([(cx, y - h * 1.32, 18), (cx + 18, y - h * 1.42, 22), (cx + 42, y - h * 1.5, 26)], "#e6ecf5", stroke="#b8c2d2", sw=3)
    s += f'<circle cx="{X-w*0.3:.1f}" cy="{y-h*0.18:.1f}" r="{h*0.12:.1f}" fill="#e8a070" stroke="{INK}" stroke-width="4"/>'
    return s


def solar_panel(X, y, s):
    out = f'<rect x="{X-4:.1f}" y="{y-s*0.6:.1f}" width="8" height="{s*0.6:.1f}" fill="#8a94a8" stroke="{INK}" stroke-width="3"/>'
    out += f'<path d="M{X-s*0.7:.1f} {y-s*0.55:.1f} L{X-s*0.5:.1f} {y-s*0.95:.1f} L{X+s*0.7:.1f} {y-s*0.95:.1f} L{X+s*0.5:.1f} {y-s*0.55:.1f} Z" fill="#2c4f9a" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
    for t in (0.33, 0.66):
        out += f'<line x1="{X-s*0.7+s*1.4*t-s*0.06:.1f}" y1="{y-s*0.55:.1f}" x2="{X-s*0.5+s*1.2*t+s*0.05:.1f}" y2="{y-s*0.95:.1f}" stroke="#7ab0ff" stroke-width="2"/>'
    out += f'<line x1="{X-s*0.6:.1f}" y1="{y-s*0.75:.1f}" x2="{X+s*0.6:.1f}" y2="{y-s*0.75:.1f}" stroke="#7ab0ff" stroke-width="2"/>'
    return out


def turbine(X, y, h, rot=20):
    s = f'<path d="M{X-6:.1f} {y:.1f} L{X-3:.1f} {y-h:.1f} L{X+3:.1f} {y-h:.1f} L{X+6:.1f} {y:.1f} Z" fill="#f4f8ff" stroke="{INK}" stroke-width="3"/>'
    for k in range(3):
        s += (f'<g transform="rotate({rot + 120*k} {X:.1f} {y-h:.1f})"><path d="M{X:.1f} {y-h:.1f} Q{X+h*0.08:.1f} {y-h-h*0.25:.1f} {X:.1f} {y-h-h*0.5:.1f} Q{X-h*0.03:.1f} {y-h-h*0.25:.1f} {X:.1f} {y-h:.1f} Z" '
              f'fill="#ffffff" stroke="{INK}" stroke-width="3"/></g>')
    return s + f'<circle cx="{X:.1f}" cy="{y-h:.1f}" r="7" fill="#7ef0ff" stroke="{INK}" stroke-width="3"/>'


def hologram(X, y, s, c):
    top = y - s * 1.6
    pts = f"{X:.1f},{top:.1f} {X+s*0.5:.1f},{top+s*0.5:.1f} {X:.1f},{top+s:.1f} {X-s*0.5:.1f},{top+s*0.5:.1f}"
    return (f'<path d="M{X-s*0.25:.1f} {y:.1f} L{X+s*0.25:.1f} {y:.1f} L{X+s*0.18:.1f} {y-s*0.18:.1f} L{X-s*0.18:.1f} {y-s*0.18:.1f} Z" fill="#4a3d6b" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M{X-s*0.15:.1f} {y-s*0.18:.1f} L{X-s*0.5:.1f} {top+s*0.5:.1f} L{X+s*0.5:.1f} {top+s*0.5:.1f} L{X+s*0.15:.1f} {y-s*0.18:.1f} Z" fill="{c}" opacity="0.18"/>'
            f'<polygon points="{pts}" fill="{c}" opacity="0.35" stroke="{c}" stroke-width="4"/>'
            f'<line x1="{X:.1f}" y1="{top:.1f}" x2="{X:.1f}" y2="{top+s:.1f}" stroke="{c}" stroke-width="2"/>'
            f'<line x1="{X-s*0.5:.1f}" y1="{top+s*0.5:.1f}" x2="{X+s*0.5:.1f}" y2="{top+s*0.5:.1f}" stroke="{c}" stroke-width="2"/>')


def maglev(X, y, w, c="#f4f8ff", stripe="#2fb0c4"):
    s = ""
    for px in (X - w * 0.42, X, X + w * 0.42):
        s += f'<rect x="{px-10:.1f}" y="{y-110:.1f}" width="20" height="110" fill="#b8bfcc" stroke="{INK}" stroke-width="4"/>'
    s += f'<rect x="{X-w/2-30:.1f}" y="{y-122:.1f}" width="{w+60:.1f}" height="16" fill="#9aa3b4" stroke="{INK}" stroke-width="4"/>'
    body = (f"M{X-w/2:.1f} {y-128:.1f} L{X-w/2:.1f} {y-170:.1f} Q{X-w/2:.1f} {y-185:.1f} {X-w/2+20:.1f} {y-185:.1f} L{X+w/2-40:.1f} {y-185:.1f} "
            f"Q{X+w/2+30:.1f} {y-180:.1f} {X+w/2+40:.1f} {y-128:.1f} Z")
    s += f'<path d="{body}" fill="{c}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
    s += f'<rect x="{X-w/2:.1f}" y="{y-150:.1f}" width="{w+30:.1f}" height="8" fill="{stripe}"/>'
    for i in range(6):
        s += f'<rect x="{X-w/2+16+i*(w-30)/6:.1f}" y="{y-176:.1f}" width="{(w-60)/7:.1f}" height="18" rx="5" fill="#9fe8f5" stroke="{INK}" stroke-width="2"/>'
    return s + f'<rect x="{X-w/2:.1f}" y="{y-128:.1f}" width="{w+40:.1f}" height="5" fill="#7ef0ff" opacity="0.8"/>'


def dome(X, y, w, c="#bff6ff", plants=True):
    r = w / 2
    s = ""
    if plants:
        s += blob([(X - r * 0.4, y - r * 0.25, r * 0.22), (X + r * 0.1, y - r * 0.35, r * 0.28), (X + r * 0.45, y - r * 0.2, r * 0.2)], "#4fd88a", sw=3)
    s += (f'<path d="M{X-r:.1f} {y:.1f} A{r:.1f} {r:.1f} 0 0 1 {X+r:.1f} {y:.1f} Z" fill="{c}" fill-opacity="0.35" stroke="{INK}" stroke-width="5"/>'
          f'<path d="M{X-r*0.7:.1f} {y:.1f} A{r*0.7:.1f} {r:.1f} 0 0 1 {X+r*0.7:.1f} {y:.1f} M{X-r*0.3:.1f} {y:.1f} A{r*0.3:.1f} {r:.1f} 0 0 1 {X+r*0.3:.1f} {y:.1f} M{X-r*0.95:.1f} {y-r*0.3:.1f} L{X+r*0.95:.1f} {y-r*0.3:.1f} M{X-r*0.75:.1f} {y-r*0.65:.1f} L{X+r*0.75:.1f} {y-r*0.65:.1f}" fill="none" stroke="{INK}" stroke-width="2" opacity="0.5"/>'
          f'<path d="M{X-r*0.6:.1f} {y-r*0.55:.1f} Q{X-r*0.45:.1f} {y-r*0.85:.1f} {X-r*0.1:.1f} {y-r*0.92:.1f}" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round" opacity="0.6"/>'
          f'<rect x="{X-r-6:.1f}" y="{y-8:.1f}" width="{w+12:.1f}" height="12" fill="#9aa3b4" stroke="{INK}" stroke-width="3"/>')
    return s


def server_tower(X, y, w, h, light="#5fff9f", seed=0):
    rr = random.Random(seed + int(X))
    s = f'<rect x="{X-w/2:.1f}" y="{y-h:.1f}" width="{w:.1f}" height="{h:.1f}" rx="6" fill="#16302a" stroke="{INK}" stroke-width="4"/>'
    for row in range(int(h / 22)):
        yy = y - h + 14 + row * 22
        s += f'<line x1="{X-w/2+8:.1f}" y1="{yy:.1f}" x2="{X+w/2-8:.1f}" y2="{yy:.1f}" stroke="#2a5a4a" stroke-width="3"/>'
        for col in range(3):
            if rr.random() < 0.6:
                s += f'<circle cx="{X-w/2+14+col*10:.1f}" cy="{yy:.1f}" r="3" fill="{light}"/>'
    return s + glow(X, y - h - 6, 14, light, 0.3)


def tesla_coil(X, y, h):
    s = (f'<path d="M{X-h*0.18:.1f} {y:.1f} L{X-h*0.12:.1f} {y-h*0.15:.1f} L{X+h*0.12:.1f} {y-h*0.15:.1f} L{X+h*0.18:.1f} {y:.1f} Z" fill="#6a5a8a" stroke="{INK}" stroke-width="4"/>'
         f'<rect x="{X-h*0.06:.1f}" y="{y-h*0.8:.1f}" width="{h*0.12:.1f}" height="{h*0.65:.1f}" fill="#d9a54a" stroke="{INK}" stroke-width="4"/>')
    for i in range(6):
        yy = y - h * 0.2 - i * h * 0.1
        s += f'<line x1="{X-h*0.06:.1f}" y1="{yy:.1f}" x2="{X+h*0.06:.1f}" y2="{yy:.1f}" stroke="#a0752a" stroke-width="3"/>'
    s += glow(X, y - h * 0.88, h * 0.22, "#9ef4ff", 0.3) + f'<circle cx="{X:.1f}" cy="{y-h*0.88:.1f}" r="{h*0.1:.1f}" fill="#c9d3e6" stroke="{INK}" stroke-width="4"/>'
    for sx in (-1, 1):
        s += (f'<path d="M{X+sx*h*0.1:.1f} {y-h*0.9:.1f} L{X+sx*h*0.22:.1f} {y-h*0.98:.1f} L{X+sx*h*0.18:.1f} {y-h*1.04:.1f} L{X+sx*h*0.32:.1f} {y-h*1.12:.1f}" '
              f'fill="none" stroke="#9ef4ff" stroke-width="4" stroke-linejoin="round"/>')
    return s


def mech(X, y, h):
    c, d = "#c9d3e6", "#8a94a8"
    s = (f'<rect x="{X-h*0.16:.1f}" y="{y-h*0.42:.1f}" width="{h*0.1:.1f}" height="{h*0.42:.1f}" fill="{d}" stroke="{INK}" stroke-width="4"/>'
         f'<rect x="{X+h*0.06:.1f}" y="{y-h*0.42:.1f}" width="{h*0.1:.1f}" height="{h*0.42:.1f}" fill="{d}" stroke="{INK}" stroke-width="4"/>'
         f'<rect x="{X-h*0.22:.1f}" y="{y-h*0.06:.1f}" width="{h*0.18:.1f}" height="{h*0.06:.1f}" fill="#5a6478" stroke="{INK}" stroke-width="3"/>'
         f'<rect x="{X+h*0.04:.1f}" y="{y-h*0.06:.1f}" width="{h*0.18:.1f}" height="{h*0.06:.1f}" fill="#5a6478" stroke="{INK}" stroke-width="3"/>'
         f'<path d="M{X-h*0.26:.1f} {y-h*0.42:.1f} L{X-h*0.3:.1f} {y-h*0.8:.1f} L{X+h*0.3:.1f} {y-h*0.8:.1f} L{X+h*0.26:.1f} {y-h*0.42:.1f} Z" fill="{c}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
         f'<rect x="{X-h*0.1:.1f}" y="{y-h*0.7:.1f}" width="{h*0.2:.1f}" height="{h*0.12:.1f}" rx="6" fill="#ffb84f" stroke="{INK}" stroke-width="3"/>'
         f'<rect x="{X-h*0.12:.1f}" y="{y-h*0.98:.1f}" width="{h*0.24:.1f}" height="{h*0.18:.1f}" rx="10" fill="{c}" stroke="{INK}" stroke-width="5"/>'
         f'<rect x="{X-h*0.08:.1f}" y="{y-h*0.93:.1f}" width="{h*0.16:.1f}" height="{h*0.05:.1f}" rx="4" fill="#ff4f6a"/>'
         f'<path d="M{X-h*0.3:.1f} {y-h*0.76:.1f} L{X-h*0.42:.1f} {y-h*0.5:.1f} L{X-h*0.38:.1f} {y-h*0.36:.1f}" fill="none" stroke="{d}" stroke-width="{h*0.07:.1f}" stroke-linecap="round" stroke-linejoin="round"/>'
         f'<path d="M{X+h*0.3:.1f} {y-h*0.76:.1f} L{X+h*0.44:.1f} {y-h*0.6:.1f} L{X+h*0.5:.1f} {y-h*0.72:.1f}" fill="none" stroke="{d}" stroke-width="{h*0.07:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
    return s


def crate(X, y, s, c="#c98a4b"):
    return (f'<rect x="{X-s/2:.1f}" y="{y-s:.1f}" width="{s:.1f}" height="{s:.1f}" fill="{c}" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{X-s/2:.1f} {y-s:.1f} L{X+s/2:.1f} {y:.1f} M{X+s/2:.1f} {y-s:.1f} L{X-s/2:.1f} {y:.1f}" stroke="{INK}" stroke-width="3" opacity="0.5"/>'
            f'<rect x="{X-s/2:.1f}" y="{y-s*0.55:.1f}" width="{s:.1f}" height="{s*0.1:.1f}" fill="#ffd36b"/>')


def arcology(X, y, w, h):
    s = ""
    for i, f in enumerate((1.0, 0.8, 0.6, 0.42)):
        tw, th = w * f, h * 0.24
        yb = y - i * th
        s += f'<rect x="{X-tw/2:.1f}" y="{yb-th:.1f}" width="{tw:.1f}" height="{th:.1f}" rx="10" fill="#f0f6ff" stroke="{INK}" stroke-width="4"/>'
        for k in range(int(tw / 34)):
            s += f'<rect x="{X-tw/2+10+k*34:.1f}" y="{yb-th*0.7:.1f}" width="20" height="{th*0.35:.1f}" rx="4" fill="#9fe8f5"/>'
        s += blob([(X - tw / 2 + 12, yb - th - 4, 10), (X + tw / 2 - 14, yb - th - 4, 12)], "#4fd88a", sw=2)
    return s + pylon(X, y - h * 0.96, h * 0.3)


def sat_dish(X, y, s):
    return (f'<path d="M{X-s*0.12:.1f} {y:.1f} L{X:.1f} {y-s*0.55:.1f} L{X+s*0.12:.1f} {y:.1f} Z" fill="#9aa3b4" stroke="{INK}" stroke-width="4"/>'
            f'<g transform="rotate(-30 {X:.1f} {y-s*0.6:.1f})"><path d="M{X-s*0.55:.1f} {y-s*0.6:.1f} A{s*0.55:.1f} {s*0.32:.1f} 0 0 0 {X+s*0.55:.1f} {y-s*0.6:.1f} Z" fill="#f0f4fa" stroke="{INK}" stroke-width="4"/>'
            f'<line x1="{X:.1f}" y1="{y-s*0.62:.1f}" x2="{X:.1f}" y2="{y-s*1.05:.1f}" stroke="{INK}" stroke-width="3"/>'
            f'<circle cx="{X:.1f}" cy="{y-s*1.07:.1f}" r="{s*0.05:.1f}" fill="#ff4f6a" stroke="{INK}" stroke-width="2"/></g>')


def launch_rocket(X, y, h, c="#f4f8ff", stripe="#e2483a"):
    w = h * 0.16
    s = f'<rect x="{X+w*1.2:.1f}" y="{y-h*0.95:.1f}" width="{w*0.4:.1f}" height="{h*0.95:.1f}" fill="none" stroke="#8a94a8" stroke-width="5"/>'
    for i in range(6):
        s += f'<line x1="{X+w*1.2:.1f}" y1="{y-h*0.15*i:.1f}" x2="{X+w*1.6:.1f}" y2="{y-h*0.15*(i+1):.1f}" stroke="#8a94a8" stroke-width="3"/>'
    s += (f'<path d="M{X-w/2:.1f} {y-h*0.12:.1f} L{X-w/2:.1f} {y-h*0.75:.1f} Q{X:.1f} {y-h*1.05:.1f} {X+w/2:.1f} {y-h*0.75:.1f} L{X+w/2:.1f} {y-h*0.12:.1f} Z" fill="{c}" stroke="{INK}" stroke-width="5" stroke-linejoin="round"/>'
          f'<path d="M{X-w/2:.1f} {y-h*0.3:.1f} L{X-w*1.1:.1f} {y-h*0.05:.1f} L{X-w/2:.1f} {y-h*0.12:.1f} Z M{X+w/2:.1f} {y-h*0.3:.1f} L{X+w*1.1:.1f} {y-h*0.05:.1f} L{X+w/2:.1f} {y-h*0.12:.1f} Z" fill="{stripe}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
          f'<rect x="{X-w/2:.1f}" y="{y-h*0.6:.1f}" width="{w:.1f}" height="{h*0.06:.1f}" fill="{stripe}"/>'
          f'<circle cx="{X:.1f}" cy="{y-h*0.72:.1f}" r="{w*0.22:.1f}" fill="#7ef0ff" stroke="{INK}" stroke-width="3"/>'
          f'<rect x="{X-w*0.9:.1f}" y="{y-h*0.12:.1f}" width="{w*1.8:.1f}" height="{h*0.12:.1f}" fill="#8a94a8" stroke="{INK}" stroke-width="4"/>')
    return s


def control_tower(X, y, h):
    return (f'<path d="M{X-h*0.08:.1f} {y:.1f} L{X-h*0.05:.1f} {y-h*0.75:.1f} L{X+h*0.05:.1f} {y-h*0.75:.1f} L{X+h*0.08:.1f} {y:.1f} Z" fill="#c9d3e6" stroke="{INK}" stroke-width="4"/>'
            f'<path d="M{X-h*0.2:.1f} {y-h*0.75:.1f} L{X-h*0.16:.1f} {y-h*0.92:.1f} L{X+h*0.16:.1f} {y-h*0.92:.1f} L{X+h*0.2:.1f} {y-h*0.75:.1f} Z" fill="#9fe8f5" stroke="{INK}" stroke-width="4"/>'
            f'<rect x="{X-h*0.17:.1f}" y="{y-h*0.98:.1f}" width="{h*0.34:.1f}" height="{h*0.06:.1f}" fill="#8a94a8" stroke="{INK}" stroke-width="3"/>'
            + glow(X, y - h * 1.05, 16, "#ff4f6a", 0.35) + f'<circle cx="{X:.1f}" cy="{y-h*1.05:.1f}" r="6" fill="#ff4f6a"/>')


def planet(X, y, r, c, ring=False, c2="#ffffff"):
    s = glow(X, y, r * 1.5, c, 0.15) + f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{c}" stroke="{INK}" stroke-width="4"/>'
    s += f'<path d="M{X-r*0.85:.1f} {y-r*0.2:.1f} Q{X:.1f} {y-r*0.4:.1f} {X+r*0.85:.1f} {y-r*0.15:.1f}" fill="none" stroke="{c2}" stroke-width="{r*0.12:.1f}" opacity="0.35"/>'
    s += f'<circle cx="{X-r*0.35:.1f}" cy="{y-r*0.35:.1f}" r="{r*0.2:.1f}" fill="#ffffff" opacity="0.3"/>'
    if ring:
        s += f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{r*1.7:.1f}" ry="{r*0.4:.1f}" fill="none" stroke="{c2}" stroke-width="{r*0.12:.1f}" transform="rotate(-15 {X:.1f} {y:.1f})" opacity="0.85"/>'
    return s


def asteroid(X, y, r, c="#8a7a90"):
    pts = []
    rr = random.Random(int(X * 7 + y))
    for i in range(9):
        a = math.tau * i / 9
        k = rr.uniform(0.75, 1.1)
        pts.append(f"{X + r*k*math.cos(a):.1f},{y + r*k*math.sin(a):.1f}")
    return (f'<polygon points="{" ".join(pts)}" fill="{c}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<circle cx="{X-r*0.3:.1f}" cy="{y-r*0.1:.1f}" r="{r*0.2:.1f}" fill="#000000" opacity="0.15"/><circle cx="{X+r*0.3:.1f}" cy="{y+r*0.25:.1f}" r="{r*0.13:.1f}" fill="#000000" opacity="0.15"/>')


def mining_rig(X, y, h):
    s = (f'<path d="M{X-h*0.3:.1f} {y:.1f} L{X:.1f} {y-h:.1f} L{X+h*0.3:.1f} {y:.1f}" fill="none" stroke="#8a94a8" stroke-width="7"/>'
         f'<path d="M{X-h*0.2:.1f} {y-h*0.33:.1f} L{X+h*0.2:.1f} {y-h*0.33:.1f} M{X-h*0.1:.1f} {y-h*0.66:.1f} L{X+h*0.1:.1f} {y-h*0.66:.1f}" stroke="#8a94a8" stroke-width="5"/>'
         f'<rect x="{X-h*0.14:.1f}" y="{y-h*0.2:.1f}" width="{h*0.28:.1f}" height="{h*0.2:.1f}" fill="#ffb84f" stroke="{INK}" stroke-width="4"/>')
    return s + glow(X, y - h, 14, "#ffb84f", 0.4) + f'<circle cx="{X:.1f}" cy="{y-h:.1f}" r="6" fill="#ffb84f"/>'


def ring_arc(X, y, r, c="#c9d3e6"):
    return (f'<path d="M{X-r:.1f} {y:.1f} A{r:.1f} {r*0.35:.1f} 0 0 1 {X+r:.1f} {y:.1f}" fill="none" stroke="{INK}" stroke-width="34" opacity="0.35"/>'
            f'<path d="M{X-r:.1f} {y:.1f} A{r:.1f} {r*0.35:.1f} 0 0 1 {X+r:.1f} {y:.1f}" fill="none" stroke="{c}" stroke-width="22"/>'
            f'<path d="M{X-r:.1f} {y:.1f} A{r:.1f} {r*0.35:.1f} 0 0 1 {X+r:.1f} {y:.1f}" fill="none" stroke="#7ef0ff" stroke-width="4" stroke-dasharray="30 20"/>')


def alien_plant(X, y, h, c):
    s = f'<path d="M{X:.1f} {y:.1f} Q{X-h*0.15:.1f} {y-h*0.5:.1f} {X:.1f} {y-h*0.85:.1f}" fill="none" stroke="#3a7a5a" stroke-width="{h*0.06+4:.1f}" stroke-linecap="round"/>'
    for a in (-60, -20, 20, 60):
        rad = math.radians(a - 90)
        ex, ey = X + math.cos(rad) * h * 0.3, y - h * 0.85 + math.sin(rad) * h * 0.3
        s += f'<path d="M{X:.1f} {y-h*0.85:.1f} Q{(X+ex)/2+10:.1f} {(y-h*0.85+ey)/2:.1f} {ex:.1f} {ey:.1f}" fill="none" stroke="{c}" stroke-width="{h*0.05:.1f}" stroke-linecap="round"/>'
        s += glow(ex, ey, h * 0.08, c, 0.4) + f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{h*0.04:.1f}" fill="#ffffff"/>'
    return s


def gear(X, y, r, c="#d9a54a"):
    pts = []
    for i in range(24):
        rr = r if i % 2 == 0 else r * 0.8
        a = math.tau * i / 24
        pts.append(f"{X + rr*math.cos(a):.1f},{y + rr*math.sin(a):.1f}")
    return (f'<polygon points="{" ".join(pts)}" fill="{c}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
            f'<circle cx="{X:.1f}" cy="{y:.1f}" r="{r*0.35:.1f}" fill="#3a2a8a" stroke="{INK}" stroke-width="3"/>')


def portal(X, y, r, c="#c9a6ff", inner="#7ef0ff"):
    return (glow(X, y, r * 1.4, inner, 0.18)
            + f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{r*0.7:.1f}" ry="{r:.1f}" fill="{inner}" opacity="0.45"/>'
            + f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{r*0.45:.1f}" ry="{r*0.7:.1f}" fill="#ffffff" opacity="0.4"/>'
            + f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{r*0.7:.1f}" ry="{r:.1f}" fill="none" stroke="{INK}" stroke-width="{r*0.18+8:.1f}"/>'
            + f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="{r*0.7:.1f}" ry="{r:.1f}" fill="none" stroke="{c}" stroke-width="{r*0.18:.1f}"/>'
            + "".join(f'<circle cx="{X + r*0.7*math.cos(math.radians(a)):.1f}" cy="{y + r*math.sin(math.radians(a)):.1f}" r="{r*0.05:.1f}" fill="#ffffff"/>' for a in range(0, 360, 45)))


def light_strip(X, y, c):
    return f'<rect x="{X-14:.1f}" y="{y-3:.1f}" width="28" height="6" rx="3" fill="{c}"/>' + glow(X, y, 14, c, 0.2)


# ======================================================================= layers
def conf(zone):
    a = 15 + (zone * 7) % 25
    return dict(mtn=([(a, 2 + zone % 4, (zone * 0.37) % 3.1)], -20 + (zone * 13) % 50),
                hills=([(10 + zone % 9, 3 + zone % 3, (zone * 0.71) % 3.1)], -5 + (zone * 5) % 15),
                trees=([(6 + zone % 7, 3 + zone % 2, (zone * 1.13) % 3.1)], (zone * 3) % 12))


def sky_layer(zone):
    z = Z(5000 + zone)
    r_ = z.rnd
    if zone in NIGHT:
        for _ in range(45):
            x, y = r_.uniform(10, W - 10), r_.uniform(15, 600)
            z.add(x, 6, lambda X, y=y, r=r_.uniform(1.5, 3.5): star_dot(X, y, r))
        pl = {9: ("#5fff9f", False), 13: ("#ffb84f", True), 14: ("#e2483a", False), 15: ("#4cc3f0", False), 16: ("#c9a6ff", True),
              17: ("#7ef0ff", True), 18: ("#ff9ef0", False), 19: ("#9ef4ff", True)}[zone]
        z.add(1400, 200, lambda X: planet(X, 180, 70, pl[0], pl[1]))
    else:
        for i in range(3):
            x, y, sc = i * W / 3 + r_.uniform(60, 400), r_.uniform(90, 380), r_.uniform(0.8, 1.2)
            z.add(x, 182 * sc, lambda X, y=y, sc=sc: blob([(X + a * sc, y + b * sc, r * sc) for a, b, r in CLOUD_PARTS], "#ffffff", stroke="#cde8f7", sw=3))
        if zone == 20:
            z.add(1400, 200, lambda X: glow(X, 200, 170, "#fff1c4", 0.35) + f'<circle cx="{X}" cy="200" r="80" fill="#ffe08a" stroke="#f5b82e" stroke-width="8"/>')
    return sky_defs(zone), "", z


def mountains_layer(zone):
    z = Z(6000 + zone)
    c = conf(zone)
    yb = make_yf(T_MTN_BACK, c["mtn"][0], c["mtn"][1])
    yfr = make_yf(T_MTN_FRONT, [(a * 0.7, k + 1, p) for a, k, p in c["mtn"][0]], c["mtn"][1] * 0.6)
    sil = FP[zone][3]
    dark = mix(sil, "#1d1236", 0.35)
    if zone in (1, 2, 6, 7, 12, 3):                        # futuristic skyline far away
        for i, x in enumerate(range(160, 1800, 150)):
            hh = 140 + (i * 47 + zone * 31) % 170
            z.add(x, 60, lambda X, hh=hh, i=i: skyscraper(X, yfr(X) + 40, 90, hh, dark, mix(FP[zone][7], "#ffffff", 0.3), seed=zone * 50 + i))
    elif zone in (8, 15):
        for x, w in ((520, 300), (1350, 380)):
            z.add(x, w / 2 + 10, lambda X, w=w: dome(X, yfr(X) + 20, w, "#e6f8ff", plants=False))
    elif zone == 16:
        for x, yy, r in ((420, 260, 70), (900, 180, 40), (1300, 300, 90), (1700, 220, 50)):
            z.add(x, r + 10, lambda X, yy=yy, r=r: asteroid(X, yy, r))
    elif zone == 17:
        z.add(960, 900, lambda X: ring_arc(X, 520, 880))
    elif zone == 18:
        for x, yy, s_ in ((500, 300, 1.4), (1300, 240, 1.7)):
            z.add(x, 260, lambda X, yy=yy, s_=s_: blob([(X + a * s_, yy + b * s_, r * s_) for a, b, r in CLOUD_PARTS], "#ff9ef0", stroke=None))
    elif zone == 19:
        for x, yy, r in ((600, 260, 90), (1350, 330, 120)):
            z.add(x, r + 10, lambda X, yy=yy, r=r: gear(X, yy, r, "#7a6ad0"))
    else:
        for x, h in ((450, 260), (980, 340), (1500, 290)):
            z.add(x, 190, lambda X, h=h: far_peak(X, yfr(X) + 40, 380, h, mix(sil, "#ffffff", 0.15)))
    pre = layer_defs(zone, ("mb", "mb"), ("mf", "mf")) + f'<path d="{gpath(yb)}" fill="url(#mb)"/>'
    post = f'<path d="{gpath(yfr)}" fill="url(#mf)"/>'
    return pre, post, z


def hills_layer(zone):
    z = Z(7000 + zone)
    c = conf(zone)
    yf = make_yf(T_HILLS, c["hills"][0], c["hills"][1])
    r_ = z.rnd
    shade = mix(FP[zone][4], "#1d3a2a", 0.25)
    for x in place(r_, 10, min_gap=60):
        y = yf(x) + 6
        rr = r_.uniform(16, 26)
        z.add(x, rr * 1.7 + 4, lambda X, y=y, rr=rr: blob([(X, y - rr, rr), (X - rr * .7, y - rr * .5, rr * .7), (X + rr * .7, y - rr * .5, rr * .7)], shade, sw=3))
    acc = FP[zone][7]
    for x in (300, 820, 1340, 1800):
        if zone in (1, 2, 7, 12, 17, 20):
            z.add(x, 30, lambda X: pylon(X, yf(X) + 6, 150, acc))
        elif zone in (4,):
            z.add(x, 40, lambda X: turbine(X, yf(X) + 6, 120, rot=x % 90))
        elif zone in (13, 14):
            z.add(x, 60, lambda X: sat_dish(X, yf(X) + 6, 70))
        elif zone in (9,):
            z.add(x, 30, lambda X: server_tower(X, yf(X) + 6, 40, 110, acc, seed=x))
    pre = layer_defs(zone, ("hl", "hills")) + f'<path d="{gpath(yf)}" fill="url(#hl)"/>' + gridge(yf, 5)
    return pre, "", z


def trees_layer(zone):
    z = Z(8000 + zone)
    c = conf(zone)
    yf = make_yf(T_TREES, c["trees"][0], c["trees"][1])
    r_ = z.rnd
    acc = FP[zone][7]

    def at(x, ext, fn):
        z.add(x, ext, lambda X: fn(X, yf(X) + 12))

    if zone == 1:
        at(1000, 120, lambda X, y: launch_rocket(X, y, 360))
        for x in (300, 600, 1450, 1750):
            at(x, 30, lambda X, y: glow_lamp(X, y, 140))
        at(1300, 50, lambda X, y: robot(X, y, 80))
    elif zone == 2:
        for x, yy, cc in ((420, 260, "#ff4fd8"), (900, 330, "#7ef0ff"), (1450, 240, "#ffe14d")):
            at(x, 100, lambda X, y, yy=yy, cc=cc: pylon(X, y, yy + 40, cc) + hover_car(X, y - yy, 70, cc))
        for x in (200, 1200, 1750):
            at(x, 30, lambda X, y: glow_lamp(X, y, 130))
    elif zone == 3:
        at(950, 260, lambda X, y: factory(X, y, 460))
        for x in (300, 1550, 1750):
            at(x, 50, lambda X, y: robot(X, y, 90, "#e8a070"))
        at(500, 40, lambda X, y: crate(X, y, 60) + crate(X + 50, y, 50))
    elif zone == 4:
        for x in (250, 420, 590, 1250, 1420, 1590):
            at(x, 80, lambda X, y: solar_panel(X, y, 110))
        for x in (900, 1820):
            at(x, 60, lambda X, y: turbine(X, y, 250, rot=x % 90))
    elif zone == 5:
        for x in (220, 520, 900, 1300, 1680):
            at(x, 100, lambda X, y: round_tree(X, y, r_.uniform(150, 200), r_.choice(["#4fd88a", "#7ef0ff", "#c9a6ff"]), "#6a5a8a"))
        for x in (720, 1100, 1500):
            at(x, 30, lambda X, y: glow_flower(X, y - 10) + glow_flower(X + 26, y - 4))
    elif zone == 6:
        for x, cc in ((300, "#ff9ef0"), (800, "#7ef0ff"), (1350, "#ffe14d"), (1750, "#c9a6ff")):
            at(x, 70, lambda X, y, cc=cc: hologram(X, y, 110, cc))
        for x, cc in ((560, "#ff4fd8"), (1080, "#4ff0ff"), (1560, "#ffe14d")):
            at(x, 70, lambda X, y, cc=cc: neon_sign(X, y - 60, 120, 70, cc))
    elif zone == 7:
        at(960, 420, lambda X, y: maglev(X, y, 700))
        for x in (180, 1750):
            at(x, 30, lambda X, y: glow_lamp(X, y, 130))
    elif zone == 8:
        for x, w in ((350, 260), (1000, 380), (1600, 280)):
            at(x, w / 2 + 10, lambda X, y, w=w: dome(X, y, w))
    elif zone == 9:
        for i, x in enumerate((220, 420, 620, 1150, 1350, 1550, 1750)):
            at(x, 40, lambda X, y, i=i: server_tower(X, y, 70, 160 + (i * 37) % 90, acc, seed=i))
        for _ in range(10):
            x, yy = r_.uniform(60, W - 60), r_.uniform(480, 720)
            z.add(x, 10, lambda X, yy=yy: star_dot(X, yy, 3, acc))
    elif zone == 10:
        at(950, 120, lambda X, y: observatory(X, y, 200))
        for x in (420, 1450):
            at(x, 50, lambda X, y: tesla_coil(X, y, 220))
        for x, s_ in ((700, 50), (1700, 60)):
            at(x, s_ * 1.2, lambda X, y, s_=s_: crystals(X, y, s_, "#9ef4ff", "#e2ffff"))
    elif zone == 11:
        at(1000, 160, lambda X, y: mech(X, y, 340))
        for x in (350, 520, 1450, 1650):
            at(x, 50, lambda X, y: crate(X, y, r_.uniform(50, 80), r_.choice(["#c98a4b", "#8a94a8", "#e8a070"])))
    elif zone == 12:
        at(980, 260, lambda X, y: arcology(X, y, 440, 420))
        for x in (300, 1700):
            at(x, 100, lambda X, y: round_tree(X, y, 160, "#4fd88a"))
    elif zone == 13:
        for x, s_ in ((350, 150), (850, 200), (1400, 170)):
            at(x, s_ * 0.6, lambda X, y, s_=s_: sat_dish(X, y, s_))
        at(1750, 30, lambda X, y: pylon(X, y, 180, acc))
    elif zone == 14:
        for x, h in ((450, 320), (1400, 380)):
            at(x, 90, lambda X, y, h=h: launch_rocket(X, y, h, "#f4f8ff", "#ffb84f"))
        at(950, 60, lambda X, y: control_tower(X, y, 260))
    elif zone == 15:
        for x, w in ((380, 220), (900, 300), (1500, 240)):
            at(x, w / 2 + 10, lambda X, y, w=w: dome(X, y, w, "#dfe6ff", plants=False))
        at(1200, 60, lambda X, y: sat_dish(X, y, 120))
        at(1780, 50, lambda X, y: robot(X, y, 80, "#dfe6ff"))
    elif zone == 16:
        for x in (400, 1100, 1700):
            at(x, 60, lambda X, y: mining_rig(X, y, 200))
        for x, s_ in ((750, 60), (1400, 70)):
            at(x, s_ * 1.2, lambda X, y, s_=s_: crystals(X, y, s_, "#c9a6ff", "#efe2ff"))
    elif zone == 17:
        for x in (300, 700, 1100, 1500, 1850):
            at(x, 30, lambda X, y: pylon(X, y, 200, acc))
        at(900, 80, lambda X, y: hover_car(X, y - 260, 80, "#c9d3e6"))
    elif zone == 18:
        for x, h, cc in ((260, 220, "#ff9ef0"), (700, 280, "#7ef0ff"), (1150, 240, "#c9a6ff"), (1600, 300, "#ff9ef0")):
            at(x, 70, lambda X, y, h=h, cc=cc: alien_plant(X, y, h, cc))
        for x, h in ((480, 200), (1400, 180)):
            at(x, h * 0.46, lambda X, y, h=h: giant_mushroom(X, y, h, "#c96bff", "#ffe1ff"))
    elif zone == 19:
        at(1000, 200, lambda X, y: portal(X, y - 170, 150, "#c9a6ff", "#9ef4ff"))
        for x, yy, r in ((350, 220, 50), (650, 320, 35), (1450, 260, 60), (1750, 340, 40)):
            at(x, r + 10, lambda X, y, yy=yy, r=r: gear(X, y - yy, r))
    elif zone == 20:
        at(960, 320, lambda X, y: portal(X, y - 240, 230, "#ffd34d", "#c9a6ff"))
        for x in (420, 1500):
            at(x, 30, lambda X, y: pylon(X, y, 260, "#ffd34d"))
    pre = layer_defs(zone, ("tr", "trees")) + f'<path d="{gpath(yf)}" fill="url(#tr)"/>' + gridge(yf, 5)
    return pre, "", z


def ground_layer(zone):
    z = Z(9000 + zone)
    base, _terms = T_GROUND
    yf = make_yf(T_GROUND)
    r_ = z.rnd
    path = gpath(yf)
    acc = FP[zone][7]
    s = (layer_defs(zone, ("gd", "ground"), ("gs", "grid")) +
         f'<clipPath id="grd"><path d="{path}"/></clipPath><path d="{path}" fill="url(#gd)"/>'
         '<g clip-path="url(#grd)" opacity="0.55">')
    for yy in (base + 30, base + 75, base + 135):                    # floor lines
        s += f'<rect x="0" y="{yy}" width="{W}" height="4" fill="url(#gs)"/>'
    for i in range(-2, 18):                                          # converging grid columns (period W/16 -> tiles)
        x = i * W / 16
        s += f'<line x1="{x:.1f}" y1="{base - 20}" x2="{x - 90:.1f}" y2="{H}" stroke="url(#gs)" stroke-width="4"/>'
    s += '</g>' + gridge(yf, 6)
    for x in place(r_, 4, lo=60, hi=W - 60, avoid=[(860, 1060)], min_gap=260):
        rr = r_.uniform(24, 34)
        z.add(x, rr * 1.8 + 6, lambda X, rr=rr: bush(X, yf(X) + 8, rr, mix(FP[zone][6], "#1d3a2a", 0.3)))
    for _ in range(14):
        x, y = r_.uniform(20, W - 20), r_.uniform(base + 40, H - 20)
        if r_.random() < 0.5:
            z.add(x, 16, lambda X, y=y: light_strip(X, y, acc))
        else:
            z.add(x, 14, lambda X, y=y: glow_flower(X, y) if zone in (5, 8, 18) else f'<ellipse cx="{X:.1f}" cy="{y:.1f}" rx="13" ry="7" fill="#c9d3e6" stroke="{INK}" stroke-width="3"/>')
    return s, "", z


# ======================================================================= sky extension
def ext_layer(zone, rnd):
    z = Z(10000 + zone)
    body = ('<defs>' + hgrad("exb", zone, "sky") + hgrad("exh", zone, "high") +
            '<linearGradient id="exv" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/>'
            '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>'
            f'<mask id="exm"><rect width="{W}" height="{H}" fill="url(#exv)"/></mask></defs>'
            f'<rect width="{W}" height="{H}" fill="url(#exb)"/><rect width="{W}" height="{H}" fill="url(#exh)" mask="url(#exm)"/>')
    if zone in NIGHT:
        for _ in range(60):
            x, y = rnd.uniform(10, W - 10), rnd.uniform(10, 1060)
            z.add(x, 6, lambda X, y=y, r=rnd.uniform(1.4, 3.2): star_dot(X, y, r))
        z.add(600, 140, lambda X: planet(X, 420, rnd.uniform(40, 70), FP[zone][7], zone % 2 == 1))
        for x, y in ((1200, 700), (1600, 300)):
            z.add(x, 40, lambda X, y=y: drone(X, y, 26))
    else:
        for i in range(3):
            x, y, sc = i * W / 3 + rnd.uniform(60, 400), rnd.uniform(520, 900), rnd.uniform(0.8, 1.2)
            z.add(x, 182 * sc, lambda X, y=y, sc=sc: blob([(X + a * sc, y + b * sc, r * sc) for a, b, r in CLOUD_PARTS], "#ffffff", stroke="#cde8f7", sw=3))
        for x, y, cc in ((450, 380, "#ff4fd8"), (1100, 250, "#7ef0ff"), (1650, 600, "#ffe14d")):
            if zone == 20:
                z.add(x, 90, lambda X, y=y, cc=cc: "".join(
                    f'<line x1="{X + math.cos(math.radians(a))*25:.1f}" y1="{y + math.sin(math.radians(a))*25:.1f}" x2="{X + math.cos(math.radians(a))*80:.1f}" y2="{y + math.sin(math.radians(a))*80:.1f}" stroke="{cc}" stroke-width="7" stroke-linecap="round"/>'
                    for a in range(0, 360, 30)))
            else:
                z.add(x, 80, lambda X, y=y, cc=cc: hover_car(X, y, 50, cc) if (x // 10) % 2 == 0 else drone(X, y, 30))
    return body, z


# ======================================================================= assemble
LAYER_NAMES = ["01_sky", "02_mountains", "03_hills", "04_trees", "05_ground"]


def doc(body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">'
            f'<defs><clipPath id="frame"><rect width="{W}" height="{H}"/></clipPath></defs>'
            f'<g transform="translate(0 420)"><g clip-path="url(#frame)">{body}</g></g></svg>')


if __name__ == "__main__":
    carry = [[] for _ in range(5)]
    ext_carry = []
    fulls = {}
    for zone in range(1, N + 1):
        name, _label = STAGES[zone - 1]
        d = os.path.join(OUT, f"fzone_{zone:02d}_{name}", "svg")
        os.makedirs(d, exist_ok=True)
        bodies, new_carry = [], []
        for li, b in enumerate((sky_layer, mountains_layer, hills_layer, trees_layer, ground_layer)):
            pre, post, z = b(zone)
            bodies.append(pre + z.svg(carry[li]) + post)
            new_carry.append(z.spill())
        carry = new_carry
        for nm, body in zip(LAYER_NAMES, bodies):
            with open(os.path.join(d, f"layer_{nm}.svg"), "w") as f:
                f.write(doc(body))
        full = "".join(bodies)
        fulls[zone] = full
        with open(os.path.join(d, "background_full.svg"), "w") as f:
            f.write(doc(full))
        body, z = ext_layer(zone, random.Random(11000 + zone))
        with open(os.path.join(d, "layer_00_sky_extension.svg"), "w") as f:
            f.write(doc(body + z.svg(ext_carry)))
        ext_carry = z.spill()

    # preview: 4 columns x 5 rows
    cells = []
    for i, zone in enumerate(range(1, N + 1)):
        row, col = divmod(i, 4)
        body = fulls[zone]
        for ident in ("skyc", "skyfade", "grd", "mb", "mf", "hl", "tr", "gd", "gs"):
            body = body.replace(f'id="{ident}"', f'id="{ident}{zone}"').replace(f'url(#{ident})', f'url(#{ident}{zone})')
        x, y = col * 480, 40 + row * 330
        cells.append(f'<g transform="translate({x} {y}) scale(0.25)"><clipPath id="c{zone}"><rect width="{W}" height="{H}"/></clipPath>'
                     f'<g clip-path="url(#c{zone})">{body}</g></g>'
                     f'<text x="{x+240}" y="{y+305}" text-anchor="middle" font-family="Arial Rounded MT Bold, Arial, sans-serif" '
                     f'font-size="24" font-weight="bold" fill="{INK}">{zone}. {STAGES[zone-1][1]}</text>')
    with open(os.path.join(OUT, "future_preview.svg"), "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">'
                f'<rect width="{W}" height="{W}" fill="#f0f4ff"/>' + "".join(cells) + "</svg>")
    print("future zones:", N)
