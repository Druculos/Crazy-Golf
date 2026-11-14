extends SceneTree
## Rasterize SVGs to PNG with real transparency (Godot's built-in ThorVG renderer).
## Usage: Godot --headless --script svg_to_png.gd -- <in.svg> <out.png> [crop_y crop_h] [<in2.svg> <out2.png> [crop_y crop_h]] ...
## crop_y/crop_h (optional, integers) cut a horizontal band out of the rendered image.

func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var i := 0
	while i < args.size():
		var src := args[i]
		var dst := args[i + 1]
		i += 2
		var crop_y := -1
		var crop_h := -1
		if i + 1 < args.size() and args[i].is_valid_int() and args[i + 1].is_valid_int():
			crop_y = args[i].to_int()
			crop_h = args[i + 1].to_int()
			i += 2
		var img := Image.new()
		var err := img.load_svg_from_string(FileAccess.get_file_as_string(src), 1.0)
		if err != OK:
			printerr("FAILED ", src, " err=", err)
			continue
		if crop_y >= 0:
			img = img.get_region(Rect2i(0, crop_y, img.get_width(), crop_h))
		img.save_png(dst)
		print("OK ", dst.get_file(), " ", img.get_size())
	quit()
