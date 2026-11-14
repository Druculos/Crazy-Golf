# Bounce Game (Godot 4.7 golf prototype)

Hit the ball as far and as high as you can through six connected zones:
Meadow → Rocky Highlands → Ancient Ruins → Jungle Temple → Mountain Shrine → Mystic Stones →
Sunny Coast → Windmill Farm → Autumn Woods → Volcano Ridge → Sky Isles → Royal Castle (1100 yd in all).

## Open it
Godot → **Import** → pick `project.godot` in this folder → **Run** (F5).

## Controls
| Key | Action |
|---|---|
| Mouse (point) or Up / Down | Aim (10°–80°): the arrow points toward the mouse cursor |
| Hold Space or left mouse | Charge power (the meter swings up and down) |
| Release | Swing |
| 1–5 or Q / E | Switch between clubs you own |
| U | Open / close the upgrades shop |
| R | Reset the ball to the tee |

## Coins, upgrades and clubs
Every shot pays 1 coin per yard, times a **stage bonus** for where the ball lands: x1 in zones 1-2, x1.5 in 3-4, x2 in 5-6,
x2.5 in 7-8, x3 in 9-10, x3.5 in 11-12 (`stage_mult()` in `scripts/main.gd`). Coin Bonus adds +20% per level on top.
Spend coins in the shop (U):

| Upgrade | Effect | Levels |
|---|---|---|
| Power | +8% launch speed per level | 10 |
| Bounce | ball bounces higher | 8 |
| Roll | less grass drag and friction, so the ball rolls further | 8 |
| Ring Boost | +5% extra speed from boost rings | 8 |
| Coin Bonus | +20% coins per shot | 10 |

## Boost rings
24 golden rings float along the course, higher the further out they are (`RINGS` in `scripts/main.gd`:
world x, height above ground). Fly through one and the ball speeds up by x1.18 (+5% per Ring Boost level) plus a
small lift, with a fire trail for 1.2 s. Each ring works once per shot and lights up again on reset.

Clubs: Wooden ×1.0 (free), Silver ×1.15 (300), Gold ×1.3 (900), Diamond ×1.5 (2500), Obsidian ×1.75 (6000).
Upgrade prices grow each level (`UPGRADES` in `scripts/main.gd`). Progress saves automatically to `user://save.cfg`;
delete that file to start over.

## How it's built
Everything is set up in code in `scripts/main.gd` (the scene `main.tscn` is just the root node):

- **Golfer:** drawn in code (`Golfer` + `Arms` classes). The arms pivot at the shoulder and hold the current club's icon;
  the backswing follows the power meter, and the ball launches at the moment the downswing reaches it.

- **Parallax:** one `Parallax2D` per layer, holding twelve zone images side by side (each 1920×1080).
  Horizontal scroll speeds are sky 0.3, mountains 0.5, hills 0.7, trees 0.85, ground 1.0. Vertical speed is 1.0 for all,
  so the sky extensions (stacked 1080 px above each sky image) come into view when the ball flies high.
  Above them is a solid `#3b9fe8` fill, so the sky never runs out.
- **Ground:** a collision line that follows the exact curve of the ground art (`ground_y()`), with walls at both ends of the world.
- **Distance:** 19.2 px = 1 yard, which matches the zone signs (100 yd per zone). The tee is at x = 960.
- **Tuning:** `BASE_SPEED`, the `CLUBS` power values, and the ball's `PhysicsMaterial` (bounce/friction) control how far shots go.

## Test mode
`Godot --path . -- --autoplay --shots=/some/folder` hits one Obsidian shot by itself and saves screenshots.

## Art and audio
- `assets/art/`: golfer rig (body, arms, celebrate pose), ball + trail sparkles/fire, tee + tee mat, hit spark,
  dust puff, grass bits, boost burst, coin, upgrade icons, UI kit (9-patch panel, buttons, power bar), distance
  flags (100-1100 yd), boost rings (back/front halves) and the logo. Most sprites are drawn at 2x and shown at 0.5 scale.
- `assets/audio/`: music (loops), ball hit, coin, grass bounce, level-up (also used, pitched up, for rings).
  See `assets/audio/CREDITS.md` and check each track's license before publishing.

## Art sources
`art_source/` holds everything used to make the art (Godot skips it thanks to `art_source/.gdignore`):
SVG/PNG versions of the zones, sky extensions, clubs and the original meadow background, the 3D 7-iron
(`golf_club.blend`), the game art SVGs (`art_source/game_art/`), and the generators in `art_source/tools/`
(`make_game_art.py` for sprites/UI, `render_logo.gd` for the logo, `contact_sheet.gd` to preview a batch,
`make_golf_zones.py --no-signs` for the ground layers used in-game). After regenerating art, re-render the PNGs with
`Godot --headless --script art_source/tools/svg_to_png.gd -- <in.svg> <out.png> [crop_y crop_h]` and copy them into `assets/`.
