extends SceneTree
## Usage: Godot --headless --script contact_sheet.gd -- <out.png> <img1.png> <img2.png> ...
## Lays images out in a grid (each fitted into a 220x220 cell) on a soft blue background.
func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var out := args[0]
	var files := args.slice(1)
	var cell := 220
	var cols := 8
	var rows := int(ceil(files.size() / float(cols)))
	var sheet := Image.create(cols * cell, rows * cell, false, Image.FORMAT_RGBA8)
	sheet.fill(Color("bfe7ff"))
	for i in files.size():
		var img := Image.load_from_file(files[i])
		img.convert(Image.FORMAT_RGBA8)
		var s := minf(1.0, (cell - 20.0) / maxf(img.get_width(), img.get_height()))
		if s < 1.0:
			img.resize(int(img.get_width() * s), int(img.get_height() * s))
		var x := (i % cols) * cell + (cell - img.get_width()) / 2
		var y := (i / cols) * cell + (cell - img.get_height()) / 2
		sheet.blend_rect(img, Rect2i(Vector2i.ZERO, img.get_size()), Vector2i(x, y))
	sheet.save_png(out)
	quit()
