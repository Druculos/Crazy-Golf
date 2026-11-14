extends SceneTree
## Renders the "Bounce Game" logo with the game's Fredoka font into a transparent PNG.
## Usage (needs a window, run from the project): Godot --path <project> --script render_logo.gd -- <out.png>
const INK := Color("1d3a2a")
var vp: SubViewport
var frames := 0


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
	vp = SubViewport.new()
	vp.size = Vector2i(1400, 620)
	vp.transparent_bg = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(vp)
	var holder := Control.new()
	holder.rotation = deg_to_rad(-5)
	holder.position = Vector2(40, 90)
	vp.add_child(holder)
	for spec in [["Bounce", 250, Color("ffd34d"), Vector2(40, -40)], ["Game", 200, Color.WHITE, Vector2(430, 230)]]:
		var shadow := _label(spec[0], spec[1], INK, 64)
		shadow.position = spec[3] + Vector2(0, 16)
		holder.add_child(shadow)
		var l := _label(spec[0], spec[1], spec[2], 64)
		l.position = spec[3]
		holder.add_child(l)
	var trail := Line2D.new()
	trail.points = PackedVector2Array([Vector2(1000, 330), Vector2(1090, 250), Vector2(1170, 230)])
	trail.width = 14
	trail.default_color = Color(1, 1, 1, 0.9)
	trail.begin_cap_mode = Line2D.LINE_CAP_ROUND
	trail.end_cap_mode = Line2D.LINE_CAP_ROUND
	holder.add_child(trail)
	var ball := TextureRect.new()
	ball.texture = load("res://assets/art/ball/ball.png")
	ball.position = Vector2(1150, 180)
	ball.size = Vector2(110, 110)
	ball.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	holder.add_child(ball)


func _process(_delta: float) -> bool:
	frames += 1
	if frames == 8:
		var img := vp.get_texture().get_image()
		img.save_png(OS.get_cmdline_user_args()[0])
		print("logo saved ", img.get_size())
		return true
	return false
