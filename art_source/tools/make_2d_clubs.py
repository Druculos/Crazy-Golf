"""Generate 5 flat 2D golf club icons (SVG, 512x512, transparent, no background elements)."""
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "golf_clubs_2d"
os.makedirs(OUT, exist_ok=True)
INK = "#1d1a2e"

# Upright layout (grip on top, head at bottom), tilted diagonally at the end.
GRIP = "M236 24 Q236 14 252 14 Q268 14 268 24 L266 190 L238 190 Z"   # slight taper toward the shaft
SHAFT = "M245 186 L259 186 L256 452 L248 452 Z"                       # tapered steel shaft
FERRULE = '<rect x="245" y="446" width="14" height="12" rx="3"/>'
HEAD = ("M244 456 L260 456 L263 476 Q266 486 280 488 L378 500 Q410 504 412 532 "
        "Q412 556 384 558 L262 552 Q236 550 236 526 L240 482 Z")
GROOVES = "".join(f'<line x1="{262 + i*3}" y1="{500 + i*9}" x2="{392 - i*2}" y2="{514 + i*8}"/>' for i in range(5))

TIERS = {
    "wood": dict(label="Wooden", grip="#3e2614", wrap="#5a3a20", shaft="#c98a4b", head="#a8642e",
                 low="#7d461d", shine="#f3c78f", groove="#6e3c17",
                 extra=('<path d="M242 498 Q320 512 404 520" fill="none" stroke="#7a4318" stroke-width="3" stroke-linecap="round"/>'
                        '<path d="M250 200 Q248 300 251 440" fill="none" stroke="#9a6233" stroke-width="3" stroke-linecap="round"/>')),
    "silver": dict(label="Silver", grip="#252a33", wrap="#3d4452", shaft="#d9dee6", head="#c3cad4",
                   low="#8e98a6", shine="#ffffff", groove="#7d8794", extra=""),
    "gold": dict(label="Gold", grip="#2a1a0c", wrap="#4a2e14", shaft="#ffd34d", head="#f7b52c",
                 low="#c9800f", shine="#fff3b0", groove="#b87510", extra=""),
    "diamond": dict(label="Diamond", grip="#1a3f63", wrap="#2c6aa0", shaft="#bff3ff", head="#7ae6ff",
                    low="#2fb0e0", shine="#ffffff", groove="#2a9fcc",
                    extra=('<path d="M262 488 L320 520 L240 520 Z" fill="#b5f3ff" opacity="0.85"/>'
                           '<path d="M320 520 L410 520 L384 558 Z" fill="#3cc4ee" opacity="0.85"/>'
                           '<path d="M320 520 L280 488 L378 500 Z" fill="#d2f8ff" opacity="0.9"/>')),
    "obsidian": dict(label="Obsidian", grip="#100c18", wrap="#2a1f3d", shaft="#3b2d55", head="#241a35",
                     low="#120c1c", shine="#b98cff", groove="#5a4384",
                     extra=('<path d="M280 488 L330 552 L378 500 Z" fill="#3a2a57"/>'
                            '<path d="M330 552 L412 532 L384 558 Z" fill="#4b3670"/>')),
}


def club_svg(t):
    body = (
        f'<g stroke="{INK}" stroke-width="7" stroke-linejoin="round">'
        f'<path d="{SHAFT}" fill="{t["shaft"]}"/>'
        f'<path d="{HEAD}" fill="{t["head"]}"/>'
        f'<g fill="{t["grip"]}">{FERRULE}</g>'
        f'<path d="{GRIP}" fill="{t["grip"]}"/>'
        f'</g>'
        f'<path d="M238 528 Q320 540 410 536 Q408 556 384 558 L262 552 Q240 550 238 528 Z" fill="{t["low"]}" opacity="0.6"/>'
        f'{t["extra"]}'
        f'<g stroke="{t["groove"]}" stroke-width="2.5" stroke-linecap="round">{GROOVES}</g>'
        f'<g stroke="{t["wrap"]}" stroke-width="5" stroke-linecap="round">'
        + "".join(f'<line x1="241" y1="{y}" x2="263" y2="{y-10}"/>' for y in range(44, 186, 18))
        + '</g>'
        f'<path d="{HEAD}" fill="none" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
        f'<path d="M243 30 L242 110" stroke="#ffffff" stroke-opacity="0.3" stroke-width="5" stroke-linecap="round"/>'
        f'<path d="M249 196 L248 330" stroke="{t["shine"]}" stroke-width="3.5" stroke-linecap="round"/>'
        f'<path d="M288 494 L372 505" stroke="{t["shine"]}" stroke-width="4.5" stroke-linecap="round"/>'
        f'<path d="M248 464 L248 478" stroke="{t["shine"]}" stroke-width="4" stroke-linecap="round"/>'
    )
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">'
            '<g transform="translate(256 256) scale(0.80) rotate(-40) translate(-290 -286)">'
            f'{body}</g></svg>')


for key, t in TIERS.items():
    with open(os.path.join(OUT, f"club_{key}.svg"), "w") as f:
        f.write(club_svg(t))

# Preview sheet: clubs only, transparent background
cells = []
pos = [(0, 40), (400, 40), (800, 40), (200, 600), (600, 600)]
for (x, y), (key, t) in zip(pos, TIERS.items()):
    inner = club_svg(t).split(">", 1)[1].rsplit("</svg>", 1)[0]
    cells.append(f'<g transform="translate({x} {y}) scale(0.78)">{inner}</g>'
                 f'<text x="{x+200}" y="{y+470}" text-anchor="middle" font-family="Arial Rounded MT Bold, Arial, sans-serif" '
                 f'font-size="38" font-weight="bold" fill="{INK}">{t["label"]}</text>')
with open(os.path.join(OUT, "golf_clubs_sheet.svg"), "w") as f:
    f.write('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200">'
            + "".join(cells) + "</svg>")
print("wrote", sorted(os.listdir(OUT)))
