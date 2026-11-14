"""Generate the game's sprite / UI / FX art as SVGs plus a render manifest.

Usage: python3 make_game_art.py <svg_out_dir> <png_out_dir> <manifest_path>
Then render: Godot --headless --script svg_to_png.gd -- <pairs from the manifest>
Everything is drawn at 2x the size it is shown in-game (scale sprites by 0.5) unless noted.
"""
import math
import os
import sys

SVG_DIR, PNG_DIR, MANIFEST = sys.argv[1], sys.argv[2], sys.argv[3]
INK = "#1d3a2a"
SHIRT, SKIN, PANTS, CAP = "#4aa3ff", "#ffd2a6", "#2f3a56", "#e2483a"
items = []


def save(group, name, w, h, body):
    d = os.path.join(SVG_DIR, group)
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(PNG_DIR, group), exist_ok=True)
    path = os.path.join(d, name + ".svg")
    with open(path, "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>')
    items.append((path, os.path.join(PNG_DIR, group, name + ".png")))


def blob(circles, fill, sw=5):
    return ("".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="{INK}" stroke-width="{sw*2}"/>' for x, y, r in circles)
            + "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>' for x, y, r in circles))


def star(cx, cy, r_out, r_in, n, rot=-90):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(rot + 180 * i / n)
        pts.append(f"{cx + r*math.cos(a):.1f},{cy + r*math.sin(a):.1f}")
    return " ".join(pts)


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


def stroke_text(cx, cy, text, height, color, width):
    sc = height / 16
    adv = {c: (8 if c == " " else 13) for c in text}
    x = cx - (sum(adv[c] for c in text) - 3) * sc / 2
    out = ""
    for c in text:
        if c in GLYPHS:
            out += (f'<path d="{GLYPHS[c]}" transform="translate({x:.1f} {cy - height/2:.1f}) scale({sc:.3f})" fill="none" '
                    f'stroke="{color}" stroke-width="{width/sc:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')
        x += adv[c] * sc
    return out


# ------------------------------------------------------------------ golfer (2x; feet at (110,360), shoulder at (114,136))
def golfer_base(face="normal"):
    s = (f'<ellipse cx="110" cy="364" rx="92" ry="18" fill="#000" opacity="0.18"/>'
         f'<rect x="76" y="228" width="26" height="120" rx="6" fill="{PANTS}" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="118" y="228" width="26" height="120" rx="6" fill="{PANTS}" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="64" y="340" width="42" height="20" rx="9" fill="#f4f4f4" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="114" y="340" width="48" height="20" rx="9" fill="#f4f4f4" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="64" y="116" width="92" height="122" rx="24" fill="{SHIRT}" stroke="{INK}" stroke-width="6"/>'
         f'<rect x="67" y="218" width="86" height="14" fill="#2b2b2b"/>'
         f'<rect x="104" y="218" width="14" height="14" fill="#f5b82e"/>'
         f'<path d="M88 116 L110 142 L132 116 Z" fill="#ffffff" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
         f'<line x1="110" y1="142" x2="110" y2="170" stroke="{INK}" stroke-width="3"/>'
         f'<circle cx="110" cy="152" r="3" fill="{INK}"/><circle cx="110" cy="164" r="3" fill="{INK}"/>'
         f'<path d="M72 150 Q74 200 70 228" fill="none" stroke="#ffffff" stroke-opacity="0.3" stroke-width="6" stroke-linecap="round"/>'
         f'<circle cx="82" cy="72" r="11" fill="{SKIN}" stroke="{INK}" stroke-width="5"/>'
         f'<circle cx="116" cy="68" r="44" fill="{SKIN}" stroke="{INK}" stroke-width="6"/>'
         f'<circle cx="132" cy="84" r="9" fill="#ff8fa3" opacity="0.5"/>')
    if face == "happy":
        s += (f'<path d="M128 64 Q138 52 148 64" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
              f'<path d="M120 84 Q136 106 152 84 Z" fill="#7a2230" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')
    else:
        s += (f'<circle cx="138" cy="62" r="6.5" fill="{INK}"/><circle cx="140" cy="60" r="2" fill="#fff"/>'
              f'<path d="M124 84 Q136 96 148 84" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
    s += (f'<path d="M70 58 A46 46 0 0 1 162 58 Z" fill="{CAP}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
          f'<path d="M92 30 Q104 20 120 18" fill="none" stroke="#ffffff" stroke-opacity="0.45" stroke-width="6" stroke-linecap="round"/>'
          f'<rect x="138" y="50" width="48" height="12" rx="6" fill="{CAP}" stroke="{INK}" stroke-width="5"/>'
          f'<circle cx="116" cy="13" r="7" fill="#ffffff" stroke="{INK}" stroke-width="4"/>')
    return s


save("golfer", "golfer_body", 220, 380, golfer_base())
fist = (f'<path d="M100 146 L44 64" stroke="{INK}" stroke-width="34" stroke-linecap="round"/>'
        f'<path d="M100 146 L76 110" stroke="{SHIRT}" stroke-width="22" stroke-linecap="round"/>'
        f'<path d="M76 110 L48 70" stroke="{SKIN}" stroke-width="20" stroke-linecap="round"/>'
        f'<circle cx="42" cy="60" r="20" fill="{SKIN}" stroke="{INK}" stroke-width="6"/>'
        f'<path d="M30 54 L54 54 M30 64 L54 64" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')
save("golfer", "golfer_celebrate", 220, 380, fist + golfer_base("happy"))
save("golfer", "golfer_arms", 64, 156,
     f'<line x1="32" y1="20" x2="32" y2="124" stroke="{INK}" stroke-width="34" stroke-linecap="round"/>'
     f'<line x1="32" y1="20" x2="32" y2="80" stroke="{SHIRT}" stroke-width="22" stroke-linecap="round"/>'
     f'<line x1="32" y1="80" x2="32" y2="120" stroke="{SKIN}" stroke-width="20" stroke-linecap="round"/>'
     f'<circle cx="32" cy="130" r="21" fill="{INK}"/><circle cx="32" cy="130" r="16" fill="{SKIN}"/>'
     f'<path d="M22 126 L42 126" stroke="{INK}" stroke-width="3" stroke-linecap="round" opacity="0.6"/>')

# ------------------------------------------------------------------ ball, trails, tee
dimples = "".join(f'<circle cx="{32+dx}" cy="{32+dy}" r="2.6" fill="#cfd6dd"/>'
                  for dx, dy in ((-8, -6), (6, -10), (10, 4), (-4, 8), (2, -1), (-12, 4), (12, -4), (-2, 14)))
save("ball", "ball", 64, 64,
     f'<circle cx="32" cy="32" r="25" fill="#ffffff" stroke="{INK}" stroke-width="6"/>{dimples}'
     f'<path d="M18 22 Q24 12 36 12" fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round"/>'
     f'<path d="M20 46 Q32 54 46 44" fill="none" stroke="#dde3e9" stroke-width="5" stroke-linecap="round"/>')
save("ball", "sparkle", 48, 48,
     f'<polygon points="{star(24, 24, 21, 6, 4)}" fill="#fff7c2" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
     f'<circle cx="24" cy="24" r="4" fill="#ffffff"/>')
save("ball", "fire_puff", 64, 64,
     f'<path d="M32 6 Q50 26 50 40 A18 18 0 0 1 14 40 Q14 26 32 6 Z" fill="#ff8a3d" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
     f'<path d="M32 22 Q42 34 42 42 A10 10 0 0 1 22 42 Q22 34 32 22 Z" fill="#ffd34d"/>')
save("tee", "tee", 32, 48,
     f'<path d="M4 6 Q16 14 28 6 L28 10 Q22 14 19 16 L17 44 L15 44 L13 16 Q10 14 4 10 Z" fill="#c98a4b" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
stripes = "".join(f'<rect x="{20 + i*40}" y="10" width="20" height="44" fill="#9bec9f" opacity="0.6"/>' for i in range(8))
save("tee", "tee_mat", 360, 70,
     f'<clipPath id="m"><rect x="6" y="10" width="348" height="44" rx="20"/></clipPath>'
     f'<rect x="6" y="14" width="348" height="48" rx="20" fill="#3e9e52" stroke="{INK}" stroke-width="5"/>'
     f'<rect x="6" y="10" width="348" height="44" rx="20" fill="#7ee08a"/>'
     f'<g clip-path="url(#m)">{stripes}</g>'
     f'<rect x="6" y="10" width="348" height="44" rx="20" fill="none" stroke="{INK}" stroke-width="5"/>'
     f'<circle cx="60" cy="32" r="6" fill="#ffffff" stroke="{INK}" stroke-width="3"/>'
     f'<circle cx="300" cy="32" r="6" fill="#ffffff" stroke="{INK}" stroke-width="3"/>')

# ------------------------------------------------------------------ FX
rays = "".join(f'<line x1="{80+50*math.cos(math.radians(a)):.1f}" y1="{80+50*math.sin(math.radians(a)):.1f}" '
               f'x2="{80+74*math.cos(math.radians(a)):.1f}" y2="{80+74*math.sin(math.radians(a)):.1f}" stroke="{INK}" stroke-width="12" stroke-linecap="round"/>'
               f'<line x1="{80+50*math.cos(math.radians(a)):.1f}" y1="{80+50*math.sin(math.radians(a)):.1f}" '
               f'x2="{80+74*math.cos(math.radians(a)):.1f}" y2="{80+74*math.sin(math.radians(a)):.1f}" stroke="#fff7c2" stroke-width="6" stroke-linecap="round"/>'
               for a in range(0, 360, 45))
save("fx", "hit_spark", 160, 160,
     rays + f'<polygon points="{star(80, 80, 52, 22, 8, -67.5)}" fill="#ffe14d" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
     f'<polygon points="{star(80, 80, 26, 12, 8, -67.5)}" fill="#ffffff"/>')
save("fx", "dust_puff", 160, 110,
     blob([(50, 70, 30), (82, 56, 38), (116, 70, 30), (80, 82, 26), (30, 84, 18), (134, 86, 16)], "#efe2c0", 5)
     + '<circle cx="70" cy="46" r="10" fill="#ffffff" opacity="0.5"/>')
blades = ""
for x, h, a in ((20, 40, -25), (44, 52, -8), (64, 36, 12), (86, 48, 25), (104, 30, 40)):
    blades += (f'<path d="M{x} 74 Q{x + a*0.3:.1f} {74 - h*0.6:.1f} {x + a*0.8:.1f} {74 - h} Q{x + a*0.3 + 8:.1f} {74 - h*0.5:.1f} {x + 9} 74 Z" '
               f'fill="#3fb45a" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
save("fx", "grass_bits", 120, 80, blades)
dash = "".join(f'<path d="M{100+82*math.cos(math.radians(a)):.1f} {100+82*math.sin(math.radians(a)):.1f} '
               f'A82 82 0 0 1 {100+82*math.cos(math.radians(a+30)):.1f} {100+82*math.sin(math.radians(a+30)):.1f}" '
               f'fill="none" stroke="#7ef0ff" stroke-width="14" stroke-linecap="round"/>' for a in range(0, 360, 45))
save("fx", "boost_burst", 200, 200,
     f'<circle cx="100" cy="100" r="82" fill="none" stroke="{INK}" stroke-width="22" opacity="0.25"/>{dash}'
     f'<circle cx="100" cy="100" r="54" fill="none" stroke="#ffffff" stroke-width="8" opacity="0.8"/>')

# ------------------------------------------------------------------ UI
save("ui", "coin", 96, 96,
     f'<circle cx="48" cy="52" r="38" fill="#c9800f" stroke="{INK}" stroke-width="6"/>'
     f'<circle cx="48" cy="46" r="38" fill="#ffd34d" stroke="{INK}" stroke-width="6"/>'
     f'<circle cx="48" cy="46" r="27" fill="none" stroke="#f5b82e" stroke-width="5"/>'
     f'<polygon points="{star(48, 46, 17, 7.5, 5)}" fill="#f5b82e" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
     f'<path d="M24 34 Q30 20 46 16" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round" opacity="0.8"/>')


def badge(color, inner):
    return (f'<rect x="8" y="14" width="112" height="108" rx="28" fill="{INK}"/>'
            f'<rect x="8" y="6" width="112" height="108" rx="28" fill="{color}" stroke="{INK}" stroke-width="6"/>'
            f'<path d="M24 26 Q30 16 46 14" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round" opacity="0.5"/>' + inner)


save("ui", "icon_power", 128, 128, badge("#ff4d5e",
     f'<path d="M72 18 L38 66 L60 66 L50 104 L88 52 L66 52 Z" fill="#ffe14d" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'))
coil = "".join(f'<path d="M40 {92 - i*12} Q64 {84 - i*12} 88 {92 - i*12}" fill="none" stroke="{INK}" stroke-width="12" stroke-linecap="round"/>'
               f'<path d="M40 {92 - i*12} Q64 {84 - i*12} 88 {92 - i*12}" fill="none" stroke="#e8edf2" stroke-width="6" stroke-linecap="round"/>' for i in range(4))
save("ui", "icon_bounce", 128, 128, badge("#3fb45a",
     f'<rect x="34" y="94" width="60" height="12" rx="6" fill="#9aa39a" stroke="{INK}" stroke-width="5"/>{coil}'
     f'<circle cx="64" cy="34" r="16" fill="#ffffff" stroke="{INK}" stroke-width="5"/>'))
save("ui", "icon_roll", 128, 128, badge("#2c7be5",
     f'<line x1="18" y1="50" x2="44" y2="50" stroke="#ffffff" stroke-width="7" stroke-linecap="round"/>'
     f'<line x1="14" y1="68" x2="40" y2="68" stroke="#ffffff" stroke-width="7" stroke-linecap="round"/>'
     f'<line x1="22" y1="86" x2="44" y2="86" stroke="#ffffff" stroke-width="7" stroke-linecap="round"/>'
     f'<circle cx="74" cy="66" r="28" fill="#ffffff" stroke="{INK}" stroke-width="6"/>'
     f'<circle cx="66" cy="58" r="3.5" fill="#cfd6dd"/><circle cx="80" cy="56" r="3.5" fill="#cfd6dd"/><circle cx="84" cy="72" r="3.5" fill="#cfd6dd"/><circle cx="70" cy="78" r="3.5" fill="#cfd6dd"/>'
     f'<line x1="40" y1="100" x2="108" y2="100" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'))
stack = "".join(f'<ellipse cx="64" cy="{96 - i*14}" rx="32" ry="11" fill="#ffd34d" stroke="{INK}" stroke-width="5"/>'
                f'<path d="M32 {96 - i*14} L32 {102 - i*14} A32 11 0 0 0 96 {102 - i*14} L96 {96 - i*14}" fill="#c9800f" stroke="{INK}" stroke-width="5"/>' for i in range(4))
save("ui", "icon_coins", 128, 128, badge("#ffb02e", stack + f'<polygon points="{star(64, 54, 9, 4, 5)}" fill="#f5b82e"/>'))
save("ui", "icon_rings", 128, 128, badge("#8a5cf6",
     f'<ellipse cx="64" cy="60" rx="24" ry="40" fill="none" stroke="{INK}" stroke-width="18"/>'
     f'<ellipse cx="64" cy="60" rx="24" ry="40" fill="none" stroke="#ffd34d" stroke-width="10"/>'
     f'<path d="M20 64 L104 64" stroke="#ffffff" stroke-width="6" stroke-linecap="round" stroke-dasharray="10 10"/>'
     f'<path d="M96 54 L110 64 L96 74" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'))

# 9-patch UI kit (1x, used with texture margins)
save("ui", "panel", 96, 96,
     '<rect x="4" y="8" width="88" height="84" rx="28" fill="#1d3a2a" opacity="0.35"/>'
     f'<rect x="4" y="4" width="88" height="84" rx="28" fill="#fff8ec" stroke="{INK}" stroke-width="7"/>')


def button(face, lip, pressed=False):
    y = 10 if pressed else 4
    lip_part = "" if pressed else f'<rect x="4" y="10" width="88" height="56" rx="18" fill="{lip}" stroke="{INK}" stroke-width="5"/>'
    return (lip_part + f'<rect x="4" y="{y}" width="88" height="56" rx="18" fill="{face}" stroke="{INK}" stroke-width="5"/>'
            f'<rect x="16" y="{y+8}" width="64" height="8" rx="4" fill="#ffffff" opacity="0.35"/>')


save("ui", "button_normal", 96, 72, button("#3fb45a", "#2a7d3c"))
save("ui", "button_hover", 96, 72, button("#5ccc72", "#2f8a43"))
save("ui", "button_pressed", 96, 72, button("#329a4a", "#2a7d3c", pressed=True))
save("ui", "button_disabled", 96, 72, button("#a7b0a7", "#7c857c"))
save("ui", "bar_frame", 96, 48, f'<rect x="4" y="4" width="88" height="40" rx="18" fill="#ffffff" fill-opacity="0.75" stroke="{INK}" stroke-width="5"/>')
save("ui", "bar_fill", 96, 48,
     '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffd34d"/>'
     '<stop offset="1" stop-color="#ff4d5e"/></linearGradient></defs>'
     f'<rect x="4" y="4" width="88" height="40" rx="18" fill="url(#g)" stroke="{INK}" stroke-width="5"/>'
     '<rect x="14" y="11" width="68" height="8" rx="4" fill="#ffffff" opacity="0.45"/>')

# ------------------------------------------------------------------ distance flags (1x; pole base at (36, 276))
FLAG_COLORS = ["#ff4d5e", "#ffb02e", "#3fb45a", "#2c7be5", "#8a5cf6", "#ff8fc7"]
for dist, col in ((d, FLAG_COLORS[(d // 100 - 1) % 6]) for d in range(100, 1200, 100)):
    save("markers", f"flag_{dist}", 170, 290,
         f'<ellipse cx="40" cy="278" rx="30" ry="9" fill="#2e9c48" stroke="{INK}" stroke-width="4"/>'
         f'<path d="M40 28 Q100 18 158 40 Q110 58 150 92 Q96 104 40 98 Z" fill="{col}" stroke="{INK}" stroke-width="6" stroke-linejoin="round"/>'
         f'<path d="M52 40 Q96 32 136 42" fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round" opacity="0.45"/>'
         + stroke_text(100, 58, str(dist), 26 if dist < 1000 else 20, "#ffffff", 6.5 if dist < 1000 else 5.5) + stroke_text(102, 82, "yd", 15, "#ffffff", 4.5)
         + f'<rect x="34" y="20" width="12" height="260" rx="6" fill="#f4f4f4" stroke="{INK}" stroke-width="4"/>'
         f'<circle cx="40" cy="20" r="10" fill="#ffd34d" stroke="{INK}" stroke-width="4"/>')

# ------------------------------------------------------------------ boost ring (back half drawn behind the ball, front half in front)
def ring_half(side):
    # ellipse centre (70,140), rx 40, ry 116; side "back" = left half, "front" = right half
    sweep = 0 if side == "back" else 1
    d = f"M70 24 A40 116 0 0 {sweep} 70 256"
    glow = f'<path d="{d}" fill="none" stroke="#7ef0ff" stroke-width="44" stroke-linecap="round" opacity="0.28"/>'
    main = (f'<path d="{d}" fill="none" stroke="{INK}" stroke-width="32" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="{"#ffc93a" if side == "back" else "#ffe680"}" stroke-width="20" stroke-linecap="round"/>')
    hi = f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round" opacity="0.7" stroke-dasharray="26 22"/>'
    return glow + main + hi


save("rings", "ring_back", 140, 280, ring_half("back"))
save("rings", "ring_front", 140, 280, ring_half("front"))

with open(MANIFEST, "w") as f:
    for svg, png in items:
        f.write(f"{svg}\n{png}\n")
print(len(items), "art files")
