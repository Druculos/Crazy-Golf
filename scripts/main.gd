extends Node2D
## Bounce Game — golf launch prototype.
## Six connected zones scroll as parallax layers. A golfer swings the club; fly through boost rings to go further,
## earn coins per yard and spend them on upgrades and better clubs.

const ZONE_W := 1920.0
const ZONE_H := 1080.0
const ZONES: Array[String] = [
	"zone_01_meadow", "zone_02_rocky_highlands", "zone_03_ancient_ruins",
	"zone_04_jungle_temple", "zone_05_mountain_shrine", "zone_06_mystic_stones",
	"zone_07_sunny_coast", "zone_08_windmill_farm", "zone_09_autumn_woods",
	"zone_10_volcano_ridge", "zone_11_sky_isles", "zone_12_royal_castle",
]
const ZONE_NAMES: Array[String] = [
	"Meadow", "Rocky Highlands", "Ancient Ruins", "Jungle Temple", "Mountain Shrine", "Mystic Stones",
	"Sunny Coast", "Windmill Farm", "Autumn Woods", "Volcano Ridge", "Sky Isles", "Royal Castle",
]
## [layer file, horizontal scroll speed]. Ground = 1.0 (moves with the world); far layers move slower.
const LAYERS := [
	["layer_01_sky", 0.3],
	["layer_02_mountains", 0.5],
	["layer_03_hills", 0.7],
	["layer_04_trees", 0.85],
	["layer_05_ground", 1.0],
]
const ART := "res://assets/art/"
const HIGH_SKY := Color("3b9fe8")      # top color of the sky extensions; fills everything above them
const INK := Color("1d3a2a")
const TEE_X := 960.0
const PX_PER_YARD := 19.2              # one zone = 100 yd, matching the distance flags
const BALL_RADIUS := 12.0
const BASE_SPEED := 1600.0             # launch speed (px/s) at full power, Wooden club, no upgrades
const SAVE_PATH := "user://save.cfg"
const CLUBS := [
	{"name": "Wooden", "file": "club_wood", "power": 1.0, "cost": 0},
	{"name": "Silver", "file": "club_silver", "power": 1.15, "cost": 300},
	{"name": "Gold", "file": "club_gold", "power": 1.3, "cost": 900},
	{"name": "Diamond", "file": "club_diamond", "power": 1.5, "cost": 2500},
	{"name": "Obsidian", "file": "club_obsidian", "power": 1.75, "cost": 6000},
]
## Upgrade shop. cost = base * growth^level
const UPGRADES := {
	"power": {"name": "Power", "desc": "+8% launch speed", "icon": "icon_power", "max": 10, "base": 60, "growth": 1.4},
	"bounce": {"name": "Bounce", "desc": "Ball bounces higher", "icon": "icon_bounce", "max": 8, "base": 80, "growth": 1.5},
	"roll": {"name": "Roll", "desc": "Ball rolls further", "icon": "icon_roll", "max": 8, "base": 70, "growth": 1.5},
	"rings": {"name": "Ring Boost", "desc": "+5% boost from rings", "icon": "icon_rings", "max": 8, "base": 120, "growth": 1.4},
	"coins": {"name": "Coin Bonus", "desc": "+20% coins per shot", "icon": "icon_coins", "max": 10, "base": 100, "growth": 1.6},
}
## Boost rings: [world x, height of the ring centre above the ground in px]. One per ~900 px, climbing higher further out.
const RINGS := [
	[1900, 640], [3000, 500], [3800, 820], [4700, 380], [5500, 900], [6400, 600],
	[7300, 1000], [8200, 500], [9100, 1100], [10000, 700], [10800, 1200],
	[11700, 800], [12600, 1300], [13500, 700], [14400, 1500], [15300, 900], [16200, 1600],
	[17100, 1000], [18000, 1800], [18900, 1100], [19800, 1900], [20700, 1300], [21600, 2000], [22400, 1000],
]
const RING_HALF_HEIGHT := 85.0         # how close to the ring centre the ball must pass
const RING_SCALE := 0.85

enum State { AIM, CHARGING, SWINGING, FLYING, DONE }

var state := State.AIM
var angle_deg := 42.0
var power := 0.0
var power_dir := 1.0
var club_index := 0
var best_yards := 0.0
var max_height := 0.0
var rest_timer := 0.0
var current_zone := 0
var coins := 0
var levels := {"power": 0, "bounce": 0, "roll": 0, "rings": 0, "coins": 0}
var unlocked: Array = [0]
var title_up := true

var tex := {}               # name -> Texture2D
var ball: Ball
var golfer: Node2D
var golfer_body: Sprite2D
var arms: Node2D
var club_sprite: Sprite2D
var address_angle := 0.0
var camera: Camera2D
var aim: AimArrow
var trail: Line2D
var fx_layer: Node2D
var ball_mat: PhysicsMaterial
var ground_mat: PhysicsMaterial
var rings := []             # [{pos, back, front, used}]
var prev_ball_pos := Vector2.ZERO
var boost_time := 0.0
var fx_timer := 0.0
var last_dust := 0.0
var clock := 0.0
var rings_hit := 0

var hud: CanvasLayer
var hud_stats: Label
var hud_coins: Label
var coin_icon: TextureRect
var hud_club: Label
var club_icon: TextureRect
var power_bar: ProgressBar
var banner: Label
var banner_tween: Tween
var shop: PanelContainer
var shop_coins: Label
var upgrade_rows := {}      # id -> {level: Label, button: Button}
var club_rows := []         # [{button: Button}]
var sfx := {}               # name -> AudioStreamPlayer
var title_layer: CanvasLayer
var title_hint: Label

# Test mode: `Godot --path . -- --autoplay --shots=/some/dir` plays one shot and saves screenshots (no saving).
var autoplay := false
var shot_dir := ""
var auto_frame := 0
var auto_reset_frame := 0


class Ball extends RigidBody2D:
	pass


class AimArrow extends Node2D:
	var angle_deg := 42.0
	var power := 0.0
	

	func _draw() -> void:
		var dir := Vector2(cos(deg_to_rad(angle_deg)), -sin(deg_to_rad(angle_deg)))
		var tip := dir * (90.0 + 160.0 * power)
		print(tip)
		var col := Color.WHITE.lerp(Color("ff4d5e"), power)
		var side := dir.orthogonal() * 18.0
		var head := PackedVector2Array([tip + dir * 26.0, tip + side, tip - side])
		draw_line(dir * 26.0, tip, Color("1d3a2a"), 13.0)
		draw_line(dir * 26.0, tip, col, 7.0)
		
		
		draw_colored_polygon(head, col)
		head.append(head[0])
		draw_polyline(head, Color("1d3a2a"), 4.0)


## Coin multiplier for where the ball lands: +0.5x for every 2 stages (zones 1-2 x1, 3-4 x1.5, 5-6 x2 ... 11-12 x3.5).
static func stage_mult(zone_index: int) -> float:
	return 1.0 + 0.5 * floori(zone_index / 2.0)


static func mult_text(m: float) -> String:
	return "x%d" % int(m) if is_equal_approx(m, roundf(m)) else "x%.1f" % m


static func ground_y(x: float) -> float:
	# Same curve as the ground layer art (identical in every zone).
	return 880.0 + 10.0 * sin(TAU * 2.0 * x / ZONE_W + 0.5) + 5.0 * sin(TAU * 5.0 * x / ZONE_W + 1.7)


## Thick cartoon outline that scales with the text size.
static func outline_for(size: int) -> int:
	return clampi(int(size * 0.6), 16, 40)


func _ready() -> void:
	# The world is built in code at 1:1. Undo any accidental move/scale of the root node in the editor
	# (a stray drag once stretched the whole game 2.2x wide).
	position = Vector2.ZERO
	scale = Vector2.ONE
	rotation = 0.0
	var args := OS.get_cmdline_user_args()
	autoplay = "--autoplay" in args
	for a in args:
		if a.begins_with("--shots="):
			shot_dir = a.trim_prefix("--shots=")
	if not autoplay:
		_load_progress()
	_load_textures()
	RenderingServer.set_default_clear_color(HIGH_SKY)
	_build_world()
	_build_ground()
	_build_markers()
	_build_player_and_ball()
	_build_camera()
	_build_hud()
	_build_shop()
	_build_title()
	_build_audio()
	_select_club(club_index)
	_apply_upgrades()
	_reset_ball()
	camera.position = _camera_target()
	camera.reset_smoothing()


func _build_audio() -> void:
	# [name, file, volume dB, how many can overlap]
	for spec in [["music", "music_main", -10.0, 1], ["hit", "ball_hit", 0.0, 2], ["coin", "coin", -6.0, 6],
			["bounce", "bounce_grass", -2.0, 3], ["upgrade", "upgrade", -4.0, 2]]:
		var p := AudioStreamPlayer.new()
		p.stream = load("res://assets/audio/%s.mp3" % spec[1])
		p.volume_db = spec[2]
		p.max_polyphony = spec[3]
		add_child(p)
		sfx[spec[0]] = p
	(sfx.music.stream as AudioStreamMP3).loop = true
	if autoplay:
		AudioServer.set_bus_mute(0, true)              # keep automated test runs silent
	sfx.music.play()


func _play(name: String, pitch := 1.0, volume_db := INF) -> void:
	var p: AudioStreamPlayer = sfx[name]
	p.pitch_scale = pitch
	if volume_db != INF:
		p.volume_db = volume_db
	p.play()


func _load_textures() -> void:
	for path in ["golfer/golfer_body", "golfer/golfer_celebrate", "golfer/golfer_arms", "ball/ball", "ball/sparkle",
			"ball/fire_puff", "tee/tee", "tee/tee_mat", "fx/hit_spark", "fx/dust_puff", "fx/grass_bits", "fx/boost_burst",
			"ui/coin", "ui/panel", "ui/button_normal", "ui/button_hover", "ui/button_pressed", "ui/button_disabled",
			"ui/bar_frame", "ui/bar_fill", "rings/ring_back", "rings/ring_front", "logo/logo"]:
		tex[path.get_file()] = load(ART + path + ".png")
	for id in UPGRADES:
		tex[UPGRADES[id].icon] = load(ART + "ui/" + UPGRADES[id].icon + ".png")


# ------------------------------------------------------------------ world
func _build_world() -> void:
	for li in LAYERS.size():
		var layer := Parallax2D.new()
		layer.name = LAYERS[li][0]
		layer.scroll_scale = Vector2(LAYERS[li][1], 1.0)   # horizontal parallax, vertical moves 1:1
		add_child(layer)
		if li == 0:
			var high := ColorRect.new()                    # endless sky above the extensions
			high.color = HIGH_SKY
			high.position = Vector2(-ZONE_W, -ZONE_H - 60000.0)
			high.size = Vector2(ZONE_W * (ZONES.size() + 2), 60002.0)
			layer.add_child(high)
		for zi in ZONES.size():
			var dir := "res://assets/zones/%s/" % ZONES[zi]
			var s := Sprite2D.new()
			s.texture = load(dir + LAYERS[li][0] + ".png")
			s.centered = false
			s.position = Vector2(zi * ZONE_W, 0.0)
			layer.add_child(s)
			if li == 0:
				var ext := Sprite2D.new()                  # sky extension stacks directly above the sky
				ext.texture = load(dir + "layer_00_sky_extension.png")
				ext.centered = false
				ext.position = Vector2(zi * ZONE_W, -ZONE_H)
				layer.add_child(ext)


func _build_ground() -> void:
	var world_w := ZONE_W * ZONES.size()
	var body := StaticBody2D.new()
	ground_mat = PhysicsMaterial.new()
	ground_mat.bounce = 0.35
	ground_mat.friction = 0.9
	body.physics_material_override = ground_mat
	# Solid ground: one convex column per 48 px slice, reaching far below the surface,
	# so even very fast balls can't slip through a thin edge.
	var x := 0.0
	while x < world_w:
		var x2 := minf(x + 48.0, world_w)
		var col := CollisionShape2D.new()
		var cps := ConvexPolygonShape2D.new()
		cps.set_point_cloud(PackedVector2Array([Vector2(x, ground_y(x) + 2.0), Vector2(x2, ground_y(x2) + 2.0),
				Vector2(x2, 3000.0), Vector2(x, 3000.0)]))     # builds the hull with the winding Godot expects
		col.shape = cps
		body.add_child(col)
		x = x2
	for wx in [0.0, world_w]:                              # end walls so the ball stays in the world
		var wall := CollisionShape2D.new()
		var seg := SegmentShape2D.new()
		seg.a = Vector2(wx, 3000.0)
		seg.b = Vector2(wx, -200000.0)
		wall.shape = seg
		body.add_child(wall)
	add_child(body)


func _build_markers() -> void:
	# Distance flags in the middle of zones 2-6 (100-500 yd from the tee).
	var s := 0.62
	for n in range(1, ZONES.size()):
		var x := n * ZONE_W + TEE_X
		var flag := Sprite2D.new()
		flag.texture = load(ART + "markers/flag_%d.png" % (n * 100))
		flag.centered = false
		flag.scale = Vector2(s, s)
		flag.position = Vector2(x - 40.0 * s, ground_y(x) - 278.0 * s + 6.0)
		add_child(flag)


func _build_player_and_ball() -> void:
	var mat := Sprite2D.new()
	mat.texture = tex.tee_mat
	mat.scale = Vector2(0.5, 0.5)
	mat.position = Vector2(TEE_X - 70.0, ground_y(TEE_X) + 4.0)
	add_child(mat)
	var tee := Sprite2D.new()
	tee.texture = tex.tee
	tee.scale = Vector2(0.6, 0.6)
	tee.position = Vector2(TEE_X, ground_y(TEE_X) - 3.0)
	add_child(tee)

	# Rings: back halves go behind the ball, front halves in front (added after the ball below).
	var rings_back := Node2D.new()
	add_child(rings_back)

	# Golfer (cut-out rig): body sprite + arm pivot at the shoulder holding the club. Art is drawn at 2x.
	var gx := TEE_X - 140.0
	golfer = Node2D.new()
	golfer.position = Vector2(gx, ground_y(gx))
	add_child(golfer)
	golfer_body = Sprite2D.new()
	golfer_body.texture = tex.golfer_body
	golfer_body.centered = false
	golfer_body.scale = Vector2(0.5, 0.5)
	golfer_body.position = -Vector2(110, 360) * 0.5         # feet at the node origin
	golfer.add_child(golfer_body)
	arms = Node2D.new()
	arms.position = Vector2(2, -112)                       # shoulder
	golfer.add_child(arms)
	club_sprite = Sprite2D.new()
	club_sprite.offset = Vector2(156, 146)                 # grip end of the club icon sits at the hands
	club_sprite.position = Vector2(0, 55)
	club_sprite.rotation = deg_to_rad(47.5)                # icon shaft angle -> along the arm
	arms.add_child(club_sprite)
	var arm_art := Sprite2D.new()                          # drawn after the club, so hands cover the grip
	arm_art.texture = tex.golfer_arms
	arm_art.centered = false
	arm_art.scale = Vector2(0.5, 0.5)
	arm_art.position = -Vector2(32, 20) * 0.5               # shoulder point of the art at the pivot
	arms.add_child(arm_art)

	trail = Line2D.new()
	trail.width = 6.0
	trail.default_color = Color(1, 1, 1, 0.55)
	trail.joint_mode = Line2D.LINE_JOINT_ROUND
	trail.begin_cap_mode = Line2D.LINE_CAP_ROUND
	add_child(trail)

	ball = Ball.new()
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = BALL_RADIUS
	shape.shape = circle
	ball.add_child(shape)
	var ball_art := Sprite2D.new()
	ball_art.texture = tex.ball
	ball_art.scale = Vector2(0.5, 0.5)
	ball.add_child(ball_art)
	ball_mat = PhysicsMaterial.new()
	ball.physics_material_override = ball_mat
	ball.continuous_cd = RigidBody2D.CCD_MODE_CAST_RAY
	ball.angular_damp = 1.5
	ball.contact_monitor = true
	ball.max_contacts_reported = 4
	ball.body_entered.connect(_on_ball_contact)
	ball.freeze = true
	add_child(ball)

	var rings_front := Node2D.new()
	add_child(rings_front)
	for r in RINGS:
		var pos := Vector2(r[0], ground_y(r[0]) - r[1])
		var back := Sprite2D.new()
		back.texture = tex.ring_back
		back.position = pos
		back.scale = Vector2.ONE * RING_SCALE
		rings_back.add_child(back)
		var front := Sprite2D.new()
		front.texture = tex.ring_front
		front.position = pos
		front.scale = Vector2.ONE * RING_SCALE
		rings_front.add_child(front)
		rings.append({"pos": pos, "back": back, "front": front, "used": false})

	fx_layer = Node2D.new()
	add_child(fx_layer)
	aim = AimArrow.new()
	add_child(aim)


func _build_camera() -> void:
	camera = Camera2D.new()
	camera.limit_left = 0
	camera.limit_right = int(ZONE_W * ZONES.size())
	camera.limit_bottom = int(ZONE_H)
	camera.position_smoothing_enabled = true
	camera.position_smoothing_speed = 6.0
	add_child(camera)
	camera.make_current()


# ------------------------------------------------------------------ UI helpers
func _make_label(size: int) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_outline_color", INK)
	l.add_theme_constant_override("outline_size", outline_for(size))
	return l


func _tex_style(t: Texture2D, margin: float, pad_x := 18.0, pad_top := 10.0, pad_bottom := 10.0) -> StyleBoxTexture:
	var sb := StyleBoxTexture.new()
	sb.texture = t
	sb.set_texture_margin_all(margin)
	sb.content_margin_left = pad_x
	sb.content_margin_right = pad_x
	sb.content_margin_top = pad_top
	sb.content_margin_bottom = pad_bottom
	return sb


func _make_button(text: String, size := 26) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", size)
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color"]:
		b.add_theme_color_override(c, Color.WHITE)
	b.add_theme_color_override("font_disabled_color", Color(1, 1, 1, 0.85))
	b.add_theme_color_override("font_outline_color", INK)
	b.add_theme_constant_override("outline_size", outline_for(size))
	# Button art has a 6 px "lip" under the face; pressed art drops the face onto it.
	b.add_theme_stylebox_override("normal", _tex_style(tex.button_normal, 24, 22, 10, 16))
	b.add_theme_stylebox_override("hover", _tex_style(tex.button_hover, 24, 22, 10, 16))
	b.add_theme_stylebox_override("pressed", _tex_style(tex.button_pressed, 24, 22, 16, 10))
	b.add_theme_stylebox_override("disabled", _tex_style(tex.button_disabled, 24, 22, 10, 16))
	return b


func _icon_rect(t: Texture2D, size: float) -> TextureRect:
	var r := TextureRect.new()
	r.texture = t
	r.custom_minimum_size = Vector2(size, size)
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	return r


# ------------------------------------------------------------------ HUD
func _build_hud() -> void:
	hud = CanvasLayer.new()
	hud.name = "HUD"
	add_child(hud)

	hud_stats = _make_label(34)
	hud_stats.position = Vector2(40, 22)
	hud.add_child(hud_stats)

	var coin_row := HBoxContainer.new()
	coin_row.position = Vector2(34, 150)
	coin_row.add_theme_constant_override("separation", 8)
	coin_icon = _icon_rect(tex.coin, 62)
	coin_row.add_child(coin_icon)
	hud_coins = _make_label(40)
	coin_row.add_child(hud_coins)
	hud.add_child(coin_row)

	var shop_btn := _make_button("Upgrades (U)", 28)
	shop_btn.position = Vector2(40, 226)
	shop_btn.pressed.connect(_toggle_shop)
	hud.add_child(shop_btn)

	club_icon = _icon_rect(null, 150)
	club_icon.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	club_icon.offset_left = -190
	club_icon.offset_right = -40
	club_icon.offset_top = 20
	club_icon.offset_bottom = 170
	hud.add_child(club_icon)

	hud_club = _make_label(30)
	hud_club.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	hud_club.offset_left = -640
	hud_club.offset_right = -200
	hud_club.offset_top = 46
	hud_club.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	hud.add_child(hud_club)

	power_bar = ProgressBar.new()
	power_bar.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	power_bar.offset_left = 40
	power_bar.offset_right = 560
	power_bar.offset_top = -150
	power_bar.offset_bottom = -104
	power_bar.max_value = 1.0
	power_bar.step = 0.001
	power_bar.show_percentage = false
	power_bar.add_theme_stylebox_override("background", _tex_style(tex.bar_frame, 20, 0, 0, 0))
	power_bar.add_theme_stylebox_override("fill", _tex_style(tex.bar_fill, 20, 0, 0, 0))
	hud.add_child(power_bar)

	var help := _make_label(26)
	help.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	help.offset_left = -780
	help.offset_right = 780
	help.offset_top = -80
	help.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	help.text = "aim with MOUSE or UP / DOWN     hold SPACE or click, release to swing     fly through rings to boost     1-5 / Q E clubs     U upgrades     R reset"
	hud.add_child(help)

	banner = _make_label(80)
	banner.set_anchors_preset(Control.PRESET_CENTER_TOP)
	banner.offset_left = -900
	banner.offset_right = 900
	banner.offset_top = 150
	banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	banner.modulate.a = 0.0
	hud.add_child(banner)


func _build_title() -> void:
	title_layer = CanvasLayer.new()
	title_layer.layer = 10
	add_child(title_layer)
	var dim := ColorRect.new()
	dim.color = Color(0.11, 0.23, 0.16, 0.35)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_layer.add_child(dim)
	var logo := TextureRect.new()
	logo.texture = tex.logo
	logo.set_anchors_preset(Control.PRESET_CENTER)
	logo.offset_left = -630
	logo.offset_right = 630
	logo.offset_top = -420
	logo.offset_bottom = 140
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_layer.add_child(logo)
	title_hint = _make_label(52)
	title_hint.text = "Press SPACE or click to play"
	title_hint.set_anchors_preset(Control.PRESET_CENTER)
	title_hint.offset_left = -600
	title_hint.offset_right = 600
	title_hint.offset_top = 190
	title_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_layer.add_child(title_hint)


func _dismiss_title() -> void:
	title_up = false
	var tw := create_tween()
	tw.tween_property(title_layer.get_child(0), "modulate:a", 0.0, 0.3)
	tw.parallel().tween_property(title_layer.get_child(1), "modulate:a", 0.0, 0.3)
	tw.parallel().tween_property(title_hint, "modulate:a", 0.0, 0.3)
	tw.tween_callback(title_layer.hide)


# ------------------------------------------------------------------ shop
func _build_shop() -> void:
	var layer := CanvasLayer.new()
	layer.name = "Shop"
	layer.layer = 5
	add_child(layer)
	shop = PanelContainer.new()
	shop.set_anchors_preset(Control.PRESET_CENTER)
	shop.custom_minimum_size = Vector2(1000, 0)
	shop.grow_horizontal = Control.GROW_DIRECTION_BOTH
	shop.grow_vertical = Control.GROW_DIRECTION_BOTH
	shop.add_theme_stylebox_override("panel", _tex_style(tex.panel, 36, 34, 26, 30))
	shop.visible = false
	layer.add_child(shop)

	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 6)
	shop.add_child(v)

	var head := HBoxContainer.new()
	var title := _make_label(52)
	title.text = "Upgrades"
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title)
	head.add_child(_icon_rect(tex.coin, 52))
	shop_coins = _make_label(40)
	head.add_child(shop_coins)
	v.add_child(head)

	for id in UPGRADES:
		var u: Dictionary = UPGRADES[id]
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 14)
		row.add_child(_icon_rect(tex[u.icon], 54))
		var name_l := _make_label(27)
		name_l.text = "%s  -  %s" % [u.name, u.desc]
		name_l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(name_l)
		var lvl := _make_label(26)
		lvl.custom_minimum_size = Vector2(140, 0)
		row.add_child(lvl)
		var btn := _make_button("", 24)
		btn.custom_minimum_size = Vector2(200, 56)
		btn.pressed.connect(_buy_upgrade.bind(id))
		row.add_child(btn)
		v.add_child(row)
		upgrade_rows[id] = {"level": lvl, "button": btn}

	var clubs_title := _make_label(40)
	clubs_title.text = "Clubs"
	v.add_child(clubs_title)
	for i in CLUBS.size():
		var c: Dictionary = CLUBS[i]
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 14)
		row.add_child(_icon_rect(load("res://assets/clubs/%s.png" % c.file), 54))
		var l := _make_label(27)
		l.text = "%s club   x%.2f power" % [c.name, c.power]
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(l)
		var btn := _make_button("", 24)
		btn.custom_minimum_size = Vector2(200, 56)
		btn.pressed.connect(_club_button.bind(i))
		row.add_child(btn)
		v.add_child(row)
		club_rows.append({"button": btn})

	var close := _make_button("Close (U)", 28)
	close.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	close.pressed.connect(_toggle_shop)
	v.add_child(close)


func _upgrade_cost(id: String) -> int:
	var u: Dictionary = UPGRADES[id]
	return int(u.base * pow(u.growth, levels[id]))


func _refresh_shop() -> void:
	shop_coins.text = "%d" % coins
	for id in UPGRADES:
		var u: Dictionary = UPGRADES[id]
		var row: Dictionary = upgrade_rows[id]
		row.level.text = "Lv %d/%d" % [levels[id], u.max]
		var maxed: bool = levels[id] >= u.max
		row.button.text = "MAX" if maxed else "%d" % _upgrade_cost(id)
		row.button.icon = null if maxed else tex.coin
		row.button.expand_icon = false
		row.button.add_theme_constant_override("icon_max_width", 30)
		row.button.disabled = maxed or coins < _upgrade_cost(id)
	for i in CLUBS.size():
		var btn: Button = club_rows[i].button
		btn.add_theme_constant_override("icon_max_width", 30)
		btn.icon = null
		if i == club_index:
			btn.text = "Equipped"
			btn.disabled = true
		elif i in unlocked:
			btn.text = "Equip"
			btn.disabled = false
		else:
			btn.text = "%d" % CLUBS[i].cost
			btn.icon = tex.coin
			btn.disabled = coins < CLUBS[i].cost


func _toggle_shop() -> void:
	if title_up or state == State.CHARGING or state == State.SWINGING or state == State.FLYING:
		return
	shop.visible = not shop.visible
	if shop.visible:
		_refresh_shop()


func _buy_upgrade(id: String) -> void:
	var cost := _upgrade_cost(id)
	if coins < cost or levels[id] >= UPGRADES[id].max:
		return
	coins -= cost
	levels[id] += 1
	_play("upgrade")
	_apply_upgrades()
	_save_progress()
	_refresh_shop()


func _club_button(i: int) -> void:
	if not i in unlocked:
		if coins < CLUBS[i].cost:
			return
		coins -= CLUBS[i].cost
		unlocked.append(i)
		_play("upgrade")
	_select_club(i)
	_save_progress()
	_refresh_shop()


func _apply_upgrades() -> void:
	ball_mat.bounce = 0.4 + 0.05 * levels.bounce
	ball_mat.friction = 0.7 * pow(0.88, levels.roll)
	ground_mat.friction = 0.9 * pow(0.88, levels.roll)


func _save_progress() -> void:
	if autoplay:
		return
	var cfg := ConfigFile.new()
	cfg.set_value("progress", "coins", coins)
	cfg.set_value("progress", "best", best_yards)
	cfg.set_value("progress", "levels", levels)
	cfg.set_value("progress", "unlocked", unlocked)
	cfg.set_value("progress", "club", club_index)
	cfg.save(SAVE_PATH)


func _load_progress() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SAVE_PATH) != OK:
		return
	coins = cfg.get_value("progress", "coins", 0)
	best_yards = cfg.get_value("progress", "best", 0.0)
	var saved: Dictionary = cfg.get_value("progress", "levels", {})
	for k in saved:
		if k in levels:
			levels[k] = saved[k]
	unlocked = cfg.get_value("progress", "unlocked", [0])
	club_index = cfg.get_value("progress", "club", 0)


# ------------------------------------------------------------------ FX
func _spawn_fx(t: Texture2D, pos: Vector2, s0: float, s1: float, dur: float, rot := 0.0, drift := Vector2.ZERO) -> void:
	var sp := Sprite2D.new()
	sp.texture = t
	sp.position = pos
	sp.scale = Vector2.ONE * s0
	sp.rotation = rot
	fx_layer.add_child(sp)
	var tw := sp.create_tween().set_parallel(true)
	tw.tween_property(sp, "scale", Vector2.ONE * s1, dur).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(sp, "modulate:a", 0.0, dur).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	if drift != Vector2.ZERO:
		tw.tween_property(sp, "position", pos + drift, dur)
	tw.chain().tween_callback(sp.queue_free)


func _on_ball_contact(_body: Node) -> void:
	if state != State.FLYING or clock - last_dust < 0.12 or ball.linear_velocity.length() < 120.0:
		return
	last_dust = clock
	_play("bounce", randf_range(0.9, 1.15), linear_to_db(clampf(ball.linear_velocity.length() / 1500.0, 0.3, 1.0)) - 2.0)
	var p := ball.position + Vector2(0, BALL_RADIUS)
	_spawn_fx(tex.dust_puff, p + Vector2(0, -16), 0.25, 0.6, 0.55, 0.0, Vector2(0, -18))
	_spawn_fx(tex.grass_bits, p + Vector2(0, -10), 0.35, 0.55, 0.45, randf_range(-0.3, 0.3), Vector2(0, -24))


func _coin_burst(amount: int) -> void:
	var n := clampi(amount / 40, 5, 14)
	var vp := get_viewport().get_visible_rect().size
	var target := coin_icon.global_position + coin_icon.size / 2.0
	for i in n:
		var c := _icon_rect(tex.coin, 54)
		c.size = Vector2(54, 54)
		c.position = vp / 2.0 + Vector2(randf_range(-120, 120), randf_range(-60, 60)) - c.size / 2.0
		hud.add_child(c)
		var tw := c.create_tween()
		tw.tween_interval(i * 0.05)
		tw.tween_property(c, "position", c.position + Vector2(0, -60), 0.18).set_ease(Tween.EASE_OUT)
		tw.tween_property(c, "position", target - c.size / 2.0, 0.45).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.tween_callback(_play.bind("coin", randf_range(0.95, 1.2)))
		tw.tween_callback(c.queue_free)
	var bump := coin_icon.create_tween()
	bump.tween_interval(0.6)
	bump.tween_property(coin_icon, "scale", Vector2(1.3, 1.3), 0.08)
	bump.tween_property(coin_icon, "scale", Vector2.ONE, 0.15)
	coin_icon.pivot_offset = coin_icon.size / 2.0


# ------------------------------------------------------------------ gameplay
func _select_club(i: int) -> void:
	i = posmod(i, CLUBS.size())
	if not i in unlocked:
		return
	club_index = i
	var t: Texture2D = load("res://assets/clubs/%s.png" % CLUBS[club_index].file)
	club_sprite.texture = t
	club_icon.texture = t


func _cycle_club(step: int) -> void:
	var i := club_index
	for _n in CLUBS.size():
		i = posmod(i + step, CLUBS.size())
		if i in unlocked:
			_select_club(i)
			return


func _reset_ball() -> void:
	state = State.AIM
	ball.freeze = true
	ball.linear_velocity = Vector2.ZERO
	ball.angular_velocity = 0.0
	ball.rotation = 0.0
	var tee_pos := Vector2(TEE_X, ground_y(TEE_X) - BALL_RADIUS - 6.0)
	ball.global_position = tee_pos
	# Also move the body in the physics server, so a reset works even mid-flight or right after freezing.
	var rid := ball.get_rid()
	PhysicsServer2D.body_set_state(rid, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(0.0, tee_pos))
	PhysicsServer2D.body_set_state(rid, PhysicsServer2D.BODY_STATE_LINEAR_VELOCITY, Vector2.ZERO)
	PhysicsServer2D.body_set_state(rid, PhysicsServer2D.BODY_STATE_ANGULAR_VELOCITY, 0.0)
	# Aim the arms + club so the club head rests just behind the ball.
	var shoulder := golfer.position + arms.position
	var v := tee_pos + Vector2(-10, 10) - shoulder
	address_angle = atan2(-v.x, v.y)
	club_sprite.scale = Vector2.ONE * clampf((v.length() - 55.0) / 407.0, 0.15, 0.6)
	arms.rotation = address_angle
	golfer_body.texture = tex.golfer_body
	trail.clear_points()
	power = 0.0
	max_height = 0.0
	current_zone = 0
	boost_time = 0.0
	rings_hit = 0
	for r in rings:
		r.used = false
		r.back.modulate = Color.WHITE
		r.front.modulate = Color.WHITE


func _press() -> void:
	if title_up:
		_dismiss_title()
		return
	if shop.visible:
		return
	if state == State.AIM:
		state = State.CHARGING
		power = 0.0
		power_dir = 1.0
	elif state == State.DONE:
		_reset_ball()


func _release() -> void:
	if state == State.CHARGING:
		_swing()


func _swing() -> void:
	# Downswing to the ball, hit it at impact, then follow through.
	state = State.SWINGING
	var tw := create_tween()
	tw.tween_property(arms, "rotation", address_angle, 0.09).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_callback(_launch)
	tw.tween_property(arms, "rotation", address_angle - deg_to_rad(215), 0.25).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)


func _launch() -> void:
	state = State.FLYING
	var speed: float = BASE_SPEED * (0.25 + 0.75 * power) * CLUBS[club_index].power * (1.0 + 0.08 * levels.power)
	var dir := Vector2(cos(deg_to_rad(angle_deg)), -sin(deg_to_rad(angle_deg)))
	ball.freeze = false
	ball.linear_velocity = dir * speed
	ball.angular_velocity = 25.0
	rest_timer = 0.0
	prev_ball_pos = ball.position
	_spawn_fx(tex.hit_spark, ball.position, 0.3, 0.9, 0.28, randf() * TAU)
	_play("hit", 0.9 + 0.3 * power)


func _check_rings() -> void:
	var a := prev_ball_pos
	var b := ball.position
	prev_ball_pos = b
	if is_equal_approx(a.x, b.x):
		return
	for r in rings:
		if r.used:
			continue
		var rx: float = r.pos.x
		if (a.x - rx) * (b.x - rx) > 0.0:
			continue                                       # did not cross this ring's x this frame
		var y := lerpf(a.y, b.y, (rx - a.x) / (b.x - a.x))
		if absf(y - r.pos.y) <= RING_HALF_HEIGHT:
			_boost(r)


func _boost(r: Dictionary) -> void:
	r.used = true
	rings_hit += 1
	var v := ball.linear_velocity
	var mult: float = 1.18 + 0.05 * levels.rings
	ball.linear_velocity = v.normalized() * (v.length() * mult + 120.0) + Vector2(0, -80)
	boost_time = 1.2
	_play("upgrade", 1.5, -6.0)
	for s in [r.back, r.front]:
		var tw: Tween = s.create_tween()
		tw.tween_property(s, "scale", Vector2.ONE * RING_SCALE * 1.25, 0.1)
		tw.tween_property(s, "scale", Vector2.ONE * RING_SCALE, 0.2)
		tw.parallel().tween_property(s, "modulate:a", 0.3, 0.3)
	_spawn_fx(tex.boost_burst, r.pos, 0.4, 1.4, 0.45)
	_show_banner("BOOST!" if rings_hit == 1 else "BOOST x%d!" % rings_hit, 0.6)


func _finish_shot() -> void:
	state = State.DONE
	ball.freeze = true
	var yards := maxf(0.0, (ball.position.x - TEE_X) / PX_PER_YARD)
	var zone := clampi(int(ball.position.x / ZONE_W), 0, ZONES.size() - 1)
	var m := stage_mult(zone)
	var earned := int(round(yards * (1.0 + 0.2 * levels.coins) * m))
	coins += earned
	best_yards = max(best_yards, yards)
	_save_progress()
	var bonus := "" if m <= 1.0 else "\n%s stage bonus!" % mult_text(m)
	_show_banner("%d yd!   +%d coins%s" % [int(round(yards)), earned, bonus], 3.0)
	if earned > 0:
		_coin_burst(earned)
	if yards >= 40.0:
		golfer_body.texture = tex.golfer_celebrate         # fist pump
		var tw := create_tween()
		tw.tween_interval(2.4)
		tw.tween_callback(func() -> void: golfer_body.texture = tex.golfer_body)


func _show_banner(text: String, hold := 1.2) -> void:
	banner.text = text
	banner.modulate.a = 1.0
	if banner_tween:
		banner_tween.kill()
	banner_tween = create_tween()
	banner_tween.tween_interval(hold)
	banner_tween.tween_property(banner, "modulate:a", 0.0, 0.8)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and not event.echo:
		var key: Key = event.keycode
		if event.pressed:
			if title_up:
				_press()
			elif key == KEY_U:
				_toggle_shop()
			elif shop.visible:
				return
			elif key >= KEY_1 and key <= KEY_5 and state == State.AIM:
				_select_club(key - KEY_1)
			elif key == KEY_Q and state == State.AIM:
				_cycle_club(-1)
			elif key == KEY_E and state == State.AIM:
				_cycle_club(1)
			elif key == KEY_R and state != State.SWINGING:
				_reset_ball()
			elif key == KEY_SPACE:
				_press()
		elif key == KEY_SPACE:
			_release()
	elif event is InputEventMouseMotion:
		_mouse_aim()
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_mouse_aim()
			_press()
		else:
			_release()


## Point the aim arrow at the mouse (works while aiming and while charging). Arrow keys still work too.
func _mouse_aim() -> void:
	if title_up or shop.visible or not (state == State.AIM or state == State.CHARGING):
		return
	var d := get_global_mouse_position() - ball.position
	if d.length() < 20.0:
		return                                             # too close to the ball to read a direction
	angle_deg = clampf(rad_to_deg(atan2(-d.y, d.x)), 10.0, 80.0)


func _process(delta: float) -> void:
	clock += delta
	match state:
		State.AIM, State.CHARGING:
			if not shop.visible and not title_up:
				if Input.is_key_pressed(KEY_UP):
					angle_deg = min(angle_deg + 40.0 * delta, 80.0)
				if Input.is_key_pressed(KEY_DOWN):
					angle_deg = max(angle_deg - 40.0 * delta, 10.0)
			if state == State.CHARGING:
				power += power_dir * delta * 0.9
				if power >= 1.0:
					power = 1.0
					power_dir = -1.0
				elif power <= 0.0:
					power = 0.0
					power_dir = 1.0
				arms.rotation = address_angle + deg_to_rad(200.0) * power   # backswing grows with power
		State.FLYING:
			_check_rings()
			trail.add_point(ball.position)
			if trail.get_point_count() > 600:
				trail.remove_point(0)
			_flight_fx(delta)
			max_height = max(max_height, (ground_y(ball.position.x) - ball.position.y - BALL_RADIUS) / PX_PER_YARD)
			var z := clampi(int(ball.position.x / ZONE_W), 0, ZONES.size() - 1)
			if z > current_zone:
				var raised := stage_mult(z) > stage_mult(current_zone)
				current_zone = z
				_show_banner(ZONE_NAMES[z] + "!" + ("\nCoins %s" % mult_text(stage_mult(z)) if raised else ""))
			var on_ground := ball.position.y > ground_y(ball.position.x) - BALL_RADIUS - 30.0
			var speed := ball.linear_velocity.length()
			if not on_ground:
				ball.linear_damp = 0.02
			elif speed < 60.0:
				ball.linear_damp = 4.0          # nearly stopped: settle quickly instead of creeping for ages
			else:
				ball.linear_damp = 0.9 * pow(0.8, levels.roll)
			if speed < 25.0 and on_ground:
				rest_timer += delta
				if rest_timer > 0.6:
					_finish_shot()
			else:
				rest_timer = 0.0

	# Unused rings pulse gently so they read as pick-ups.
	var pulse := RING_SCALE * (1.0 + 0.035 * sin(clock * 4.0))
	for r in rings:
		if not r.used:
			r.back.scale = Vector2.ONE * pulse
			r.front.scale = Vector2.ONE * pulse
	if title_up:
		title_hint.modulate.a = 0.6 + 0.4 * sin(clock * 3.0)
	aim.visible = (state == State.AIM or state == State.CHARGING) and not title_up
	aim.position = ball.position
	aim.angle_deg = angle_deg
	aim.power = power
	aim.queue_redraw()
	camera.position = camera.position.lerp(_camera_target(), clampf(delta * 5.0, 0.0, 1.0))
	_update_hud()
	if autoplay:
		_autoplay_step()


func _physics_process(_delta: float) -> void:
	# Safety net: if the ball ever ends up under the grass, put it back on top and bounce it up.
	if state != State.FLYING:
		return
	var floor_y := ground_y(ball.position.x) - BALL_RADIUS
	if ball.position.y > floor_y + 14.0:
		var v := ball.linear_velocity
		var rid := ball.get_rid()
		PhysicsServer2D.body_set_state(rid, PhysicsServer2D.BODY_STATE_TRANSFORM, Transform2D(0.0, Vector2(ball.position.x, floor_y - 1.0)))
		PhysicsServer2D.body_set_state(rid, PhysicsServer2D.BODY_STATE_LINEAR_VELOCITY, Vector2(v.x, -absf(v.y) * ball_mat.bounce))


func _flight_fx(delta: float) -> void:
	fx_timer -= delta
	if boost_time > 0.0:
		boost_time -= delta
		if fx_timer <= 0.0:
			fx_timer = 0.03
			_spawn_fx(tex.fire_puff, ball.position + Vector2(randf_range(-6, 6), randf_range(-6, 6)), 0.7, 0.25, 0.35,
					ball.linear_velocity.angle() + PI / 2.0)
			if randf() < 0.4:
				_spawn_fx(tex.sparkle, ball.position + Vector2(randf_range(-20, 20), randf_range(-20, 20)), 0.6, 0.2, 0.5)
	elif ball.linear_velocity.length() > 2400.0 and fx_timer <= 0.0:
		fx_timer = 0.06
		_spawn_fx(tex.sparkle, ball.position + Vector2(randf_range(-10, 10), randf_range(-10, 10)), 0.5, 0.15, 0.4)


func _camera_target() -> Vector2:
	var t := ball.position
	if state == State.FLYING:
		t.x += clampf(ball.linear_velocity.x * 0.25, 0.0, 500.0)
	else:
		t.x += 300.0
	t.y = min(t.y + 120.0, ZONE_H / 2.0)
	return t


func _update_hud() -> void:
	var yards := maxf(0.0, (ball.position.x - TEE_X) / PX_PER_YARD)
	var height := maxf(0.0, (ground_y(ball.position.x) - ball.position.y - BALL_RADIUS) / PX_PER_YARD)
	hud_stats.text = "Distance: %d yd\nHeight: %d yd   (max %d)\nBest: %d yd" % [
		roundi(yards), roundi(height), roundi(max_height), roundi(best_yards)]
	hud_coins.text = str(coins)
	var c: Dictionary = CLUBS[club_index]
	var zone_now := clampi(int(ball.position.x / ZONE_W), 0, ZONES.size() - 1)
	hud_club.text = "%s club   x%.2f power\nAngle %d°   %s   coins %s" % [
		c.name, c.power, int(angle_deg), ZONE_NAMES[zone_now], mult_text(stage_mult(zone_now))]
	power_bar.value = power


# ------------------------------------------------------------------ test mode
func _snap(tag: String) -> void:
	if shot_dir == "":
		return
	var img := get_viewport().get_texture().get_image()
	img.resize(960, 540)
	img.save_png("%s/shot_%s.png" % [shot_dir, tag])


func _autoplay_step() -> void:
	auto_frame += 1
	match auto_frame:
		6:
			_snap("title")
		8:
			_press()                    # dismiss the title
		20:
			coins = 1500
			unlocked = [0, 1]
			_toggle_shop()
		30:
			_snap("shop")
		36, 38:
			# mouse-aim check: move the cursor relative to the ball and read the angle back
			var off := Vector2(300, -300) if auto_frame == 36 else Vector2(400, -100)
			get_viewport().warp_mouse(get_viewport().get_canvas_transform() * (ball.position + off))
		37, 39:
			_mouse_aim()
			print("AUTOPLAY mouse aim -> %d deg" % roundi(angle_deg))
		34:
			_toggle_shop()
			unlocked = [0, 1, 2, 3, 4]
			_select_club(4)
			_reset_ball()
		40:
			_snap("address")
			angle_deg = 38.0            # lines up with the first boost ring at this power
			_press()
		64:
			_snap("backswing")
			power = 0.85
			_release()
		78:
			_snap("followthrough")
	if state == State.FLYING and rings_hit > 0 and boost_time > 0.9 and not has_meta("boost_snapped"):
		set_meta("boost_snapped", true)
		_snap("boost")
	if auto_frame == 200:
		_snap("flight")
	if OS.has_environment("BALL_DEBUG") and state == State.FLYING and auto_frame % 10 == 0:
		print("DBG f=%d pos=%s vel=%s rings=%d" % [auto_frame, ball.position.round(), ball.linear_velocity.round(), rings_hit])
	if auto_reset_frame == 0 and (auto_frame == 900 or (auto_frame > 220 and state == State.DONE and auto_frame % 20 == 0)):
		_snap("done")
		print("AUTOPLAY state=%s distance=%d yd max_height=%d yd rings=%d coins=%d" % [
			State.keys()[state], int((ball.position.x - TEE_X) / PX_PER_YARD), int(max_height), rings_hit, coins])
		auto_reset_frame = auto_frame
	elif auto_reset_frame > 0 and auto_frame == auto_reset_frame + 10:
		_snap("celebrate")
		_reset_ball()
	elif auto_reset_frame > 0 and auto_frame == auto_reset_frame + 40:
		print("AUTOPLAY after reset: state=%s ball_x=%d (tee %d)" % [State.keys()[state], int(ball.global_position.x), int(TEE_X)])
		get_tree().quit()
