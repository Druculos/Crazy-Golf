"""Per-stage color themes shared by the zone and sky-extension generators (and mirrored in the game for the
endless high sky). Each layer of a stage is filled with a horizontal gradient: it starts at the blend of the
previous stage's color and this one, holds this stage's color through the middle, and ends at the blend with
the next stage, so every seam matches exactly on both sides.

keys: sky = sky colour at the top of the main sky layer (horizon gets a white haze on top of it)
      high = colour at the top of the sky extension (and everything above it in the game)
      mb / mf = far / near mountains, hills, trees = the two hill bands, ground + stripe = the fairway
"""

W = 1920

PALETTE = {
    1:  dict(sky="#5ec8ff", high="#3b9fe8", mb="#9fdcc0", mf="#7ccfa2", hills="#55c36b", trees="#3fb45a", ground="#6fd66f", stripe="#8be58a"),  # Meadow
    2:  dict(sky="#7cc6ee", high="#4f97d6", mb="#d5e2e8", mf="#a9c2bd", hills="#78ad7a", trees="#62a265", ground="#86c983", stripe="#c9e6cf"),  # Rocky Highlands (frosty)
    3:  dict(sky="#7fd0f5", high="#4aa3e0", mb="#e2d6b0", mf="#c8c493", hills="#93bf5e", trees="#7fb354", ground="#99d16c", stripe="#b4dd88"),  # Ancient Ruins (sunny olive)
    4:  dict(sky="#4fbfe6", high="#2f8fc9", mb="#7fcf9a", mf="#4cb576", hills="#2e9b50", trees="#21843d", ground="#43b558", stripe="#5ac56c"),  # Jungle Temple (deep green)
    5:  dict(sky="#f6b7d3", high="#e58fb8", mb="#f6dbe8", mf="#ebb9cf", hills="#eda3c2", trees="#7cc37b", ground="#8fd686", stripe="#f7c7db"),  # Mountain Shrine (sakura pink)
    6:  dict(sky="#8ea9f0", high="#6a7fd6", mb="#c0b8e6", mf="#a19bd8", hills="#5fb39a", trees="#4aa58c", ground="#6ccaa4", stripe="#89d9b9"),  # Mystic Stones (dusk purple)
    7:  dict(sky="#4fd2ff", high="#2fa8e6", mb="#ace8e1", mf="#89dccb", hills="#7fd47c", trees="#e9d7a1", ground="#f2dfa6", stripe="#f8eac3"),  # Sunny Coast (sand)
    8:  dict(sky="#78cfff", high="#47a6e6", mb="#c4e6a8", mf="#a6d98c", hills="#93cf5b", trees="#cdd85c", ground="#aade6b", stripe="#dbe98c"),  # Windmill Farm (wheat)
    9:  dict(sky="#f8c987", high="#e0a35c", mb="#ebc89e", mf="#dcab7b", hills="#d98c3f", trees="#c97130", ground="#c9b55b", stripe="#ddc979"),  # Autumn Woods (amber)
    10: dict(sky="#e3906a", high="#b5603f", mb="#a1908a", mf="#82746f", hills="#62705d", trees="#4f574c", ground="#6e7c5e", stripe="#808d6c"),  # Volcano Ridge (smoky)
    11: dict(sky="#a3e2ff", high="#73c3f0", mb="#dbf3ff", mf="#c2e8f8", hills="#92e2b2", trees="#72d5a2", ground="#a2e7ba", stripe="#c6f1d5"),  # Sky Isles (pastel air)
    12: dict(sky="#6eaaff", high="#4a83e6", mb="#cad5f1", mf="#adbbe4", hills="#61c075", trees="#50af67", ground="#70d380", stripe="#90e19c"),  # Royal Castle (regal blue)
    13: dict(sky="#c2e7ff", high="#8fc9f0", mb="#f1f8fc", mf="#dceaf4", hills="#eef5fa", trees="#dfeaf2", ground="#f6fafd", stripe="#e3edf5"),  # Frozen Peaks (snow)
    14: dict(sky="#f7cf7d", high="#e3a94f", mb="#f2d9a3", mf="#e6bf80", hills="#ebc882", trees="#ddb26c", ground="#f1d89d", stripe="#f6e5b9"),  # Desert Oasis (sand)
    15: dict(sky="#c9b6ff", high="#9c84e8", mb="#dccbf6", mf="#c5b1f0", hills="#9fd28b", trees="#7cc27b", ground="#90d784", stripe="#b8e7a8"),  # Mushroom Grove (violet)
    16: dict(sky="#ffc4e2", high="#f59ac8", mb="#ffdcee", mf="#ffc3df", hills="#b9f0d1", trees="#f7aacb", ground="#bdeec9", stripe="#e9fff1"),  # Candy Land (pink + mint)
    17: dict(sky="#2c3170", high="#151842", mb="#4b508c", mf="#3d417a", hills="#30695a", trees="#285a4d", ground="#3e7a5f", stripe="#4e8a6f"),  # Starlight Summit (night)
    18: dict(sky="#72e4f0", high="#2bb8d6", mb="#b8f1eb", mf="#8fe4dc", hills="#5fd0b8", trees="#f2cba3", ground="#f5ddb2", stripe="#fbeacd"),  # Coral Lagoon (turquoise)
    19: dict(sky="#c4eacb", high="#7cc4a0", mb="#dbf0df", mf="#b7e1c3", hills="#6fbf80", trees="#4ea867", ground="#80cf7b", stripe="#a0dc97"),  # Bamboo Forest (misty jade)
    20: dict(sky="#ffc077", high="#e8873f", mb="#f6d09a", mf="#e9b470", hills="#d9aa4b", trees="#c9943b", ground="#e3c265", stripe="#efd489"),  # Golden Savanna (sunset gold)
    21: dict(sky="#dccbff", high="#a98ce8", mb="#eadff9", mf="#d5c4f2", hills="#b494e1", trees="#9e7cd2", ground="#a9d68b", stripe="#c8a8ec"),  # Lavender Fields (lilac)
    22: dict(sky="#3c206e", high="#1a0f3d", mb="#5b3b90", mf="#4b307b", hills="#3e2b67", trees="#302256", ground="#3f6f6a", stripe="#4f8a80"),  # Neon City (magenta night)
    23: dict(sky="#f7a97c", high="#d9733f", mb="#eaa47c", mf="#d6835c", hills="#c96c47", trees="#7fae5a", ground="#9fcf70", stripe="#b8db8a"),  # Red Rock Canyon (terracotta)
    24: dict(sky="#c2e5ff", high="#8cc8f5", mb="#ffffff", mf="#eef6ff", hills="#e4f1fb", trees="#d6e9f8", ground="#c9f0d2", stripe="#e7fbea"),  # Cloud Kingdom (pastel white)
    25: dict(sky="#6d5c9e", high="#3a2e66", mb="#7f71aa", mf="#665a95", hills="#4b6c5b", trees="#3d5b4d", ground="#608b65", stripe="#75a179"),  # Spooky Hollow (dusk purple)
    26: dict(sky="#4b70b9", high="#26407a", mb="#8090d7", mf="#6b79c5", hills="#5b90b9", trees="#4b7ba9", ground="#60b4a1", stripe="#7dc9b7"),  # Crystal Caverns (deep blue)
    27: dict(sky="#ffda8c", high="#f0b24a", mb="#fbe4a9", mf="#f3d086", hills="#90d06b", trees="#70c05b", ground="#90d97b", stripe="#b1e797"),  # Golden Palace (gold)
}
N_ZONES = len(PALETTE)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t=0.5):
    ra, rb = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(round(ra[i] + (rb[i] - ra[i]) * t) for i in range(3))


def edge_colors(zone, key):
    """(left edge, own, right edge) colours for one layer of a stage."""
    own = PALETTE[zone][key]
    left = mix(PALETTE[zone - 1][key], own) if zone > 1 else own
    right = mix(own, PALETTE[zone + 1][key]) if zone < N_ZONES else own
    return left, own, right


def hgrad(gid, zone, key):
    left, own, right = edge_colors(zone, key)
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{W}" y2="0">'
            f'<stop offset="0" stop-color="{left}"/><stop offset="0.3" stop-color="{own}"/>'
            f'<stop offset="0.7" stop-color="{own}"/><stop offset="1" stop-color="{right}"/></linearGradient>')
