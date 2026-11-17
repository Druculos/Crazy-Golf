extends SceneTree
## Renders thumbnail / cover images for Bounce Game from the game's own art: the Meadow tee, the golfer
## finishing a swing, and the ball flying through a boost ring with a fire trail, under the logo.
## Usage (needs a window, run from the project):
##   Godot --path <project> --script art_source/tools/render_thumbnail.gd -- <out_dir>
## Writes into <out_dir>:
##   thumbnail_1920x1080.png, thumbnail_1280x720.png   16:9 (store pages, video, social)
##   itch_cover_630x500.png                            itch.io cover (rendered at 2x, then scaled down)

const INK := Color("1d3a2a")
const ART := "res://assets/art/"
const SUN_X := 1550.0                   # where the sun sits in the Meadow sky art
const LAYERS := [
	["layer_01_sky", 0.3], ["layer_02_mountains", 0.5], ["layer_03_hills", 0.7],
	["layer_04_trees", 0.85], ["layer_05_ground", 1.0],
]
const ZONES := ["zone_01_meadow", "zone_02_rocky_highlands"]
const T_RING := 0.6                     # where the boost ring sits along the ball's flight (0..1)
const T_BALL := 0.8                     # where the ball is now

## One entry per image. All positions are in that image's pixels.
##   cam: world x at the left edge (sets the parallax)   shift_y: moves the whole world up
##   sun_x: where the sun ends up (tucked behind the logo, so it glows around the lettering)
##   tee_x / rig: tee position and golfer size (x in-game size)
##   p1 / p2: control and end point of the ball's flight curve (it starts on the tee)
##   logo: [position, scale]   flag_x: the distance flag   ring: boost ring scale   ball: ball scale
const SHOTS := [
	{"size": Vector2i(1920, 1080), "files": [["thumbnail_1920x1080.png", Vector2i(1920, 1080)],
			["thumbnail_1280x720.png", Vector2i(1280, 720)]],
		"cam": 520.0, "shift_y": 0.0, "sun_x": 470.0, "tee_x": 620.0, "rig": 2.0,
		"p1": Vector2(1250, 330), "p2": Vector2(1880, 40), "logo": [Vector2(60, 70), 0.85],
		"flag_x": 1580.0, "ring": 1.35, "ball": 1.25},
	{"size": Vector2i(1260, 1000), "files": [["itch_cover_630x500.png", Vector2i(630, 500)]],
		"cam": 640.0, "shift_y": -70.0, "sun_x": 380.0, "tee_x": 450.0, "rig": 1.8,
		"p1": Vector2(820, 560), "p2": Vector2(1330, 200), "logo": [Vector2(40, 60), 0.8],
		"flag_x": 1100.0, "ring": 1.2, "ball": 1.15},
]

var viewports: Array[SubViewport] = []
var frames := 0


class Shot:
	var cfg: Dictionary
	var p0: Vector2

	func _init(c: Dictionary) -> void:
		cfg = c
		p0 = Vector2(c.tee_x, ground(c.tee_x) - 12.0 * c.rig)

	## Ground height at image x: same curve as main.gd ground_y(), in world coordinates.
	func ground(cx: float) -> float:
		var x: float = cx + cfg.cam
		return 880.0 + 10.0 * sin(TAU * 2.0 * x / 1920.0 + 0.5) + 5.0 * sin(TAU * 5.0 * x / 1920.0 + 1.7) + cfg.shift_y

	func bez(t: float) -> Vector2:
		return (1.0 - t) * (1.0 - t) * p0 + 2.0 * t * (1.0 - t) * cfg.p1 + t * t * cfg.p2

	func tangent(t: float) -> Vector2:
		return (2.0 * (1.0 - t) * (cfg.p1 - p0) + 2.0 * t * (cfg.p2 - cfg.p1)).normalized()


func _sprite(parent: Node, path: String, pos: Vector2, s: float, rot := 0.0, alpha := 1.0) -> Sprite2D:
	var sp := Sprite2D.new()
	sp.texture = load(path)
	sp.position = pos
	sp.scale = Vector2.ONE * s
	sp.rotation = rot
	sp.modulate.a = alpha
	parent.add_child(sp)
	return sp


func _label(text: String, size: int, color: Color, outline: int) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", load("res://assets/fonts/FredokaOne.tres"))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", INK)
	l.add_theme_constant_override("outline_size", outline)
	return l


func _initialize() -> void:
	for cfg in SHOTS:
		var vp := SubViewport.new()
		vp.size = cfg.size
		vp.msaa_2d = Viewport.MSAA_4X
		vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		root.add_child(vp)
		viewports.append(vp)
		var scene := Node2D.new()
		vp.add_child(scene)
		var shot := Shot.new(cfg)
		_build_background(scene, shot)
		_build_tee_and_golfer(scene, shot)
		_build_flight(scene, shot)
		_build_logo(scene, shot)


func _build_background(scene: Node2D, shot: Shot) -> void:
	var cfg := shot.cfg
	for layer in LAYERS:
		var off: float = -cfg.cam * layer[1]
		var y: float = cfg.shift_y
		if layer[0] == "layer_01_sky":
			off = cfg.sun_x - SUN_X                        # free the ball's path from the sun
			y = 0.0                                        # keep the sun low enough to hide behind the logo
		for zi in ZONES.size():
			var s := Sprite2D.new()
			s.texture = load("res://assets/zones/%s/%s.png" % [ZONES[zi], layer[0]])
			s.centered = false
			s.position = Vector2(off + zi * 1920.0, y)
			scene.add_child(s)
	var fx: float = cfg.flag_x                             # a distance flag out on the fairway
	var flag := Sprite2D.new()
	flag.texture = load(ART + "markers/flag_100.png")
	flag.centered = false
	flag.scale = Vector2.ONE * 0.75
	flag.position = Vector2(fx - 40.0 * 0.75, shot.ground(fx) - 278.0 * 0.75 + 6.0)
	scene.add_child(flag)


func _build_tee_and_golfer(scene: Node2D, shot: Shot) -> void:
	var rig: float = shot.cfg.rig
	var tx: float = shot.cfg.tee_x
	var gy := shot.ground(tx)
	_sprite(scene, ART + "tee/tee_mat.png", Vector2(tx - 70.0 * rig, gy + 4.0 * rig), 0.5 * rig)
	_sprite(scene, ART + "tee/tee.png", Vector2(tx, gy - 3.0 * rig), 0.6 * rig)

	# Golfer rig, built exactly like main.gd's, just scaled up and posed at the end of the swing.
	var gx := tx - 140.0 * rig
	var golfer := Node2D.new()
	golfer.position = Vector2(gx, shot.ground(gx))
	golfer.scale = Vector2.ONE * rig
	scene.add_child(golfer)
	var body := Sprite2D.new()
	body.texture = load(ART + "golfer/golfer_body.png")
	body.centered = false
	body.scale = Vector2(0.5, 0.5)
	body.position = -Vector2(110, 360) * 0.5
	golfer.add_child(body)
	var arms := Node2D.new()
	arms.position = Vector2(2, -112)
	arms.rotation = deg_to_rad(128.0)                  # follow-through: arms and club up over the shoulder
	golfer.add_child(arms)
	var club := Sprite2D.new()
	club.texture = load("res://assets/clubs/club_gold.png")
	club.offset = Vector2(156, 146)
	club.position = Vector2(0, 55)
	club.rotation = deg_to_rad(47.5)
	club.scale = Vector2.ONE * 0.28
	arms.add_child(club)
	var arm_art := Sprite2D.new()
	arm_art.texture = load(ART + "golfer/golfer_arms.png")
	arm_art.centered = false
	arm_art.scale = Vector2(0.5, 0.5)
	arm_art.position = -Vector2(32, 20) * 0.5
	arms.add_child(arm_art)


func _build_flight(scene: Node2D, shot: Shot) -> void:
	var cfg := shot.cfg
	var k_size: float = cfg.ring / 1.35                 # effects shrink with the ring on smaller layouts
	var ring_pos := shot.bez(T_RING)
	var ring_rot := shot.tangent(T_RING).angle()
	_sprite(scene, ART + "rings/ring_back.png", ring_pos, cfg.ring, ring_rot)

	var trail := Line2D.new()
	for i in 61:
		trail.add_point(shot.bez(T_BALL * i / 60.0))
	trail.width = 34.0 * k_size
	var wc := Curve.new()
	wc.add_point(Vector2(0.0, 0.15))
	wc.add_point(Vector2(1.0, 1.0))
	trail.width_curve = wc
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 0.1))
	g.set_color(1, Color(1, 1, 1, 0.95))
	trail.gradient = g
	trail.joint_mode = Line2D.LINE_JOINT_ROUND
	trail.begin_cap_mode = Line2D.LINE_CAP_ROUND
	trail.end_cap_mode = Line2D.LINE_CAP_ROUND
	trail.antialiased = true
	scene.add_child(trail)

	# Fire trail after the boost ring: flames point back along the path and grow toward the ball.
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var t := T_RING + 0.03
	while t < T_BALL - 0.012:
		var k := (t - T_RING) / (T_BALL - T_RING)
		var p := shot.bez(t) + shot.tangent(t).orthogonal() * rng.randf_range(-7, 7) * k_size
		_sprite(scene, ART + "ball/fire_puff.png", p, lerpf(0.7, 1.6, k) * k_size,
				shot.tangent(t).angle() - PI / 2.0 + rng.randf_range(-0.15, 0.15), lerpf(0.75, 1.0, k))
		t += 0.02
	for i in 6:
		var tt := lerpf(T_RING + 0.02, T_BALL - 0.02, i / 5.0)
		var off := shot.tangent(tt).orthogonal() * (55.0 if i % 2 == 0 else -55.0) * k_size
		_sprite(scene, ART + "ball/sparkle.png", shot.bez(tt) + off, rng.randf_range(0.6, 0.95) * k_size, rng.randf() * TAU)

	var ball_pos := shot.bez(T_BALL)
	_sprite(scene, ART + "ball/ball.png", ball_pos, cfg.ball, 0.6)
	_sprite(scene, ART + "rings/ring_front.png", ring_pos, cfg.ring, ring_rot)

	# Coins popping out of the ring.
	for c in [[Vector2(-190, -30), 0.7, -0.3], [Vector2(-130, 135), 0.62, 0.4], [Vector2(40, 185), 0.72, -0.2],
			[Vector2(185, 125), 0.56, 0.5], [Vector2(-70, -185), 0.52, 0.2], [Vector2(-265, 85), 0.46, 0.1]]:
		_sprite(scene, ART + "ui/coin.png", ring_pos + c[0] * k_size, c[1] * k_size, c[2])


func _build_logo(scene: Node2D, shot: Shot) -> void:
	# Same lettering as art_source/tools/render_logo.gd, without its little ball (the real one is flying).
	var holder := Control.new()
	holder.rotation = deg_to_rad(-5)
	holder.position = shot.cfg.logo[0]
	holder.scale = Vector2.ONE * shot.cfg.logo[1]
	scene.add_child(holder)
	for spec in [["Bounce", 250, Color("ffd34d"), Vector2(0, -40)], ["Game", 200, Color.WHITE, Vector2(390, 230)]]:
		var shadow := _label(spec[0], spec[1], INK, 64)
		shadow.position = spec[3] + Vector2(0, 16)
		holder.add_child(shadow)
		var l := _label(spec[0], spec[1], spec[2], 64)
		l.position = spec[3]
		holder.add_child(l)


func _process(_delta: float) -> bool:
	frames += 1
	if frames < 8:
		return false
	var out_dir: String = OS.get_cmdline_user_args()[0]
	DirAccess.make_dir_recursive_absolute(out_dir)
	for i in SHOTS.size():
		var img := viewports[i].get_texture().get_image()
		img.convert(Image.FORMAT_RGB8)
		for f in SHOTS[i].files:
			var out := img.duplicate() as Image
			if out.get_size() != f[1]:
				out.resize(f[1].x, f[1].y, Image.INTERPOLATE_LANCZOS)
			out.save_png(out_dir.path_join(f[0]))
			print("saved ", f[0])
	return true
