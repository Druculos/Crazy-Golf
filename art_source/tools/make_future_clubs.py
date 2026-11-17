"""Five futuristic club icons (same shape as make_2d_clubs.py, so they swing the same in game).

Usage: python3 make_future_clubs.py <svg_out_dir>   -> club_future_<key>.svg (512x512, transparent)
"""
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "future_clubs"
os.makedirs(OUT, exist_ok=True)
INK = "#1d1a2e"
GRIP = "M236 24 Q236 14 252 14 Q268 14 268 24 L266 190 L238 190 Z"
SHAFT = "M245 186 L259 186 L256 452 L248 452 Z"
FERRULE = '<rect x="245" y="446" width="14" height="12" rx="3"/>'
HEAD = ("M244 456 L260 456 L263 476 Q266 486 280 488 L378 500 Q410 504 412 532 "
        "Q412 556 384 558 L262 552 Q236 550 236 526 L240 482 Z")

# key: (name, metal, darker metal, glow, grip, grip glow)
TIERS = {
    "neon": ("Neon", "#2a3350", "#1a2038", "#4ff0ff", "#151a2c", "#4ff0ff"),
    "plasma": ("Plasma", "#3a2450", "#24163a", "#ff4fd8", "#1c1228", "#ff9ef0"),
    "quantum": ("Quantum", "#1f4a44", "#123430", "#7dff6b", "#0f2420", "#c8ff9f"),
    "nova": ("Nova", "#e8e2f0", "#b8b0c8", "#ffc94f", "#2a2438", "#ffe08a"),
    "singularity": ("Singularity", "#1a1424", "#0c0814", "#b98cff", "#0a0610", "#e2ccff"),
}


def club(metal, dark, glow, grip, grip_glow):
    circuit = (f'<path d="M262 512 L300 512 L310 522 L360 522 M282 532 L330 532 L338 540 L392 540 M300 500 L300 512" '
               f'fill="none" stroke="{glow}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
               f'<circle cx="360" cy="522" r="4.5" fill="{glow}"/><circle cx="392" cy="540" r="4.5" fill="{glow}"/>')
    body = (
        f'<path d="{HEAD}" fill="none" stroke="{glow}" stroke-width="22" stroke-linejoin="round" opacity="0.28"/>'   # neon halo
        f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
        f'<path d="{SHAFT}" fill="{metal}"/>'
        f'<path d="{HEAD}" fill="{metal}"/>'
        f'<g fill="{dark}">{FERRULE}</g>'
        f'<path d="{GRIP}" fill="{grip}"/>'
        f'</g>'
        f'<path d="M238 528 Q320 540 410 536 Q408 556 384 558 L262 552 Q240 550 238 528 Z" fill="{dark}" opacity="0.7"/>'
        + circuit +
        f'<path d="M252 196 L251 440" stroke="{glow}" stroke-width="4" stroke-linecap="round"/>'                      # light strip
        + "".join(f'<rect x="238" y="{y}" width="28" height="5" rx="2" fill="{grip_glow}"/>' for y in (40, 80, 120, 160))
        + f'<path d="{HEAD}" fill="none" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
        f'<path d="M244 456 L260 456" stroke="{glow}" stroke-width="5"/>'
        f'<path d="M288 494 L372 505" stroke="#ffffff" stroke-width="4" stroke-linecap="round" opacity="0.5"/>'
        f'<circle cx="252" cy="20" r="8" fill="{grip_glow}" stroke="{INK}" stroke-width="3"/>'
    )
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'
            '<g transform="translate(256 256) scale(0.80) rotate(-40) translate(-290 -286)">'
            f'{body}</g></svg>')


for key, (_name, *cols) in TIERS.items():
    with open(os.path.join(OUT, f"club_future_{key}.svg"), "w") as f:
        f.write(club(*cols))
print("future clubs:", list(TIERS))
