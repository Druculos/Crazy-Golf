"""Build a 7-iron golf club in Blender and save it as a .blend project.

Usage (headless):
  Blender --background --factory-startup --python build_golf_club.py -- <out_dir> [--no-render] [--samples=N]

Writes <out_dir>/golf_club.blend and preview renders in <out_dir>/renders/.
Real-world scale (meters). Shaft runs along +Z, face points -Y (Blender front),
toe points +X, lowest point of the club sits on Z = 0.
"""
import bpy
import bmesh
import math
import os
import sys
from mathutils import Euler, Matrix, Quaternion, Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_DIR = os.path.abspath(argv[0]) if argv and not argv[0].startswith("--") else os.getcwd()
DO_RENDER = "--no-render" not in argv
SAMPLES = 128
for a in argv:
    if a.startswith("--samples="):
        SAMPLES = int(a.split("=", 1)[1])
os.makedirs(os.path.join(OUT_DIR, "renders"), exist_ok=True)

scene = bpy.context.scene

# --------------------------------------------------------------------------- inspect + reset
print("INSPECT objects:", [(o.name, o.type) for o in bpy.data.objects])
print("INSPECT armatures:", [a.name for a in bpy.data.armatures],
      "actions:", [a.name for a in bpy.data.actions])
active = bpy.context.view_layer.objects.active
if active is not None and active.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
for blocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.curves):
    for d in list(blocks):
        if d.users == 0:
            blocks.remove(d)

us = scene.unit_settings
us.system = 'METRIC'
us.scale_length = 1.0
us.length_unit = 'CENTIMETERS'


def new_collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


COL_CLUB = new_collection("GolfClub")
COL_PRES = new_collection("Presentation")


# --------------------------------------------------------------------------- materials
def principled(mat):
    try:
        mat.use_nodes = True
    except Exception:
        pass
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    out = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if out is None:
        out = nt.nodes.new('ShaderNodeOutputMaterial')
    if bsdf is None:
        bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
        nt.links.new(bsdf.outputs[0], out.inputs['Surface'])
    return nt, bsdf


def set_input(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value


def make_material(name, color, metallic, roughness, coat=0.0, bump=None):
    m = bpy.data.materials.new(name)
    nt, b = principled(m)
    set_input(b, "Base Color", (*color, 1.0))
    set_input(b, "Metallic", metallic)
    set_input(b, "Roughness", roughness)
    if coat:
        set_input(b, "Coat Weight", coat)
        set_input(b, "Coat Roughness", 0.04)
    # Solid-mode viewport colors match the shader
    m.diffuse_color = (*color, 1.0)
    m.metallic = metallic
    m.roughness = roughness
    if bump:  # procedural micro-detail (Blender-only; exporters keep color/metal/roughness)
        scale_vec, noise_scale, strength = bump
        tc = nt.nodes.new('ShaderNodeTexCoord')
        mp = nt.nodes.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = scale_vec
        nz = nt.nodes.new('ShaderNodeTexNoise')
        nz.inputs['Scale'].default_value = noise_scale
        set_input(nz, 'Detail', 4.0)
        bp = nt.nodes.new('ShaderNodeBump')
        bp.inputs['Strength'].default_value = strength
        set_input(bp, 'Distance', 0.0002)
        nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
        nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
        nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
        nt.links.new(bp.outputs['Normal'], b.inputs['Normal'])
    return m


CHROME = make_material("Chrome_Polished", (0.80, 0.81, 0.83), 1.0, 0.05)
SATIN = make_material("Steel_Satin", (0.66, 0.67, 0.69), 1.0, 0.22, bump=((1.0, 60.0, 60.0), 200.0, 0.08))
GUNMETAL = make_material("Steel_Gunmetal", (0.16, 0.17, 0.19), 1.0, 0.30)
RUBBER = make_material("Rubber_Grip", (0.022, 0.022, 0.025), 0.0, 0.78, bump=((1.0, 1.0, 1.0), 2500.0, 0.25))
FERRULE = make_material("Ferrule_Gloss_Black", (0.008, 0.008, 0.009), 0.0, 0.12, coat=1.0)
HEAD_MATS = [CHROME, SATIN, GUNMETAL]          # head material slots: 0 chrome, 1 satin, 2 gunmetal


# --------------------------------------------------------------------------- helpers
def bm_to_mesh(bm, name, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return me


def append_bm(dst, src_bm):
    tmp = bpy.data.meshes.new("_tmp")
    src_bm.to_mesh(tmp)
    src_bm.free()
    dst.from_mesh(tmp)   # from_mesh appends to existing geometry
    bpy.data.meshes.remove(tmp)


def lathe(profile, segments=48):
    """Revolve a (radius, z) profile around Z. Profiles start/end on the axis -> closed solid."""
    bm = bmesh.new()
    vs = [bm.verts.new((r, 0.0, z)) for r, z in profile]
    es = [bm.edges.new((vs[i], vs[i + 1])) for i in range(len(vs) - 1)]
    bmesh.ops.spin(bm, geom=vs + es, cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=2 * math.pi, steps=segments, use_merge=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm


def assign_by(bm, rule):
    for f in bm.faces:
        c = f.calc_center_median()
        f.material_index = rule(math.hypot(c.x, c.y), c.z)


def frame(origin, x, y, z):
    m = Matrix.Identity(4)
    for r in range(3):
        m[r][0], m[r][1], m[r][2], m[r][3] = x[r], y[r], z[r], origin[r]
    return m


def catmull_closed(pts, samples=4):
    out, n = [], len(pts)
    for i in range(n):
        p0, p1, p2, p3 = (Vector(pts[(i + k) % n]) for k in (-1, 0, 1, 2))
        for s in range(samples):
            t = s / samples
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t))
    return out


def rounded_rect(w, h, r, seg=6):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90),
                       (-w / 2 + r, -h / 2 + r, 180), (w / 2 - r, -h / 2 + r, 270)):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# --------------------------------------------------------------------------- head (built in "head frame")
# Head frame: X = heel->toe, Y = face->back (face points -Y), Z = up from the sole.
LOFT = math.radians(34.0)          # 7-iron loft
LIE = math.radians(62.0)           # lie angle
TAN_L = math.tan(LOFT)
W0, WT, ZT = 0.019, 0.0065, 0.048  # sole width, top-line thickness, face height
CAV_DEPTH = 0.0040


def y_front(z):
    return TAN_L * z


def thick(z):
    return W0 - (W0 - WT) * (z / ZT)


HOSEL_PT = Vector((0.003, 0.010, 0.012))                       # point on the shaft axis (u = 0)
HEAD_TO_CLUB = Matrix.Rotation(math.radians(90) - LIE, 4, 'Y') @ Matrix.Translation(-HOSEL_PT)

OUTLINE_CTRL = [  # (x, z) face silhouette, heel-bottom -> sole -> toe -> top line -> heel
    (0.0020, 0.0040), (0.0120, 0.0008), (0.0300, 0.0000), (0.0500, 0.0000), (0.0640, 0.0012),
    (0.0730, 0.0045), (0.0785, 0.0110), (0.0805, 0.0210), (0.0800, 0.0310), (0.0770, 0.0395),
    (0.0710, 0.0455), (0.0630, 0.0480), (0.0520, 0.0465), (0.0350, 0.0410), (0.0180, 0.0350),
    (0.0060, 0.0305), (-0.0010, 0.0260), (-0.0025, 0.0160), (-0.0015, 0.0085),
]
outline = catmull_closed(OUTLINE_CTRL, 4)

bm = bmesh.new()
front = [bm.verts.new((p.x, y_front(p.y), p.y)) for p in outline]
back = [bm.verts.new((p.x, y_front(p.y) + thick(p.y), p.y)) for p in outline]
f_front = bm.faces.new(front)
f_back = bm.faces.new(list(reversed(back)))
sides = [bm.faces.new((front[i], front[(i + 1) % len(front)], back[(i + 1) % len(back)], back[i]))
         for i in range(len(front))]
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.normal_update()
f_front.material_index = 1                        # milled satin face
for f in sides:                                   # satin sole + top line (anti-glare), chrome toe/heel
    f.material_index = 1 if abs(f.normal.z) > 0.5 else 0

# Cavity back: polished rim -> gunmetal wall -> brushed floor
n_back = f_back.normal.copy()
rim = bmesh.ops.inset_region(bm, faces=[f_back], thickness=0.0052, depth=0.0, use_even_offset=True)
for f in rim['faces']:
    f.material_index = 0
wall = bmesh.ops.inset_region(bm, faces=[f_back], thickness=0.0006, depth=0.0, use_even_offset=True)
for f in wall['faces']:
    f.material_index = 2
bmesh.ops.translate(bm, verts=list(f_back.verts), vec=-n_back * CAV_DEPTH)
f_back.material_index = 1

head_me = bm_to_mesh(bm, "Club_Head_body", HEAD_MATS)
head_tmp = bpy.data.objects.new("Club_Head_body", head_me)
COL_CLUB.objects.link(head_tmp)

# Face grooves: boolean-cut once during construction (geometry, not a live modifier)
U_F = Vector((0, math.sin(LOFT), math.cos(LOFT)))       # up along the face
N_F = Vector((0, -math.cos(LOFT), math.sin(LOFT)))      # face normal (out of the face)
X_H = Vector((1, 0, 0))
cut_bm = bmesh.new()
for k in range(9):
    s = 0.0045 + k * 0.0036
    c = Vector((0.038, 0, 0)) + U_F * s + N_F * 0.000575
    bmesh.ops.create_cube(cut_bm, size=1.0, matrix=frame(c, X_H * 0.050, U_F * 0.0008, N_F * 0.00185))
cut_me = bm_to_mesh(cut_bm, "GrooveCutter", [GUNMETAL])
cutter = bpy.data.objects.new("GrooveCutter", cut_me)
COL_CLUB.objects.link(cutter)
mod = head_tmp.modifiers.new("Grooves", 'BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.solver = 'EXACT'
mod.object = cutter
try:
    mod.material_mode = 'TRANSFER'
except Exception:
    pass
dg = bpy.context.evaluated_depsgraph_get()
dg.update()
grooved = bpy.data.meshes.new_from_object(head_tmp.evaluated_get(dg))
print("GROOVES: faces", len(head_me.polygons), "->", len(grooved.polygons),
      "| materials", [m.name if m else None for m in grooved.materials])
bpy.data.objects.remove(head_tmp, do_unlink=True)
bpy.data.objects.remove(cutter, do_unlink=True)
bpy.data.meshes.remove(head_me)
bpy.data.meshes.remove(cut_me)

hb = bmesh.new()
hb.from_mesh(grooved)
canon = {CHROME.name: 0, SATIN.name: 1, GUNMETAL.name: 2}
names_in = [m.name if m else None for m in grooved.materials]
for f in hb.faces:
    nm = names_in[f.material_index] if f.material_index < len(names_in) else None
    f.material_index = canon.get(nm, 2)
bpy.data.meshes.remove(grooved)
print("HEAD verts after grooves:", len(hb.verts))

# Medallion in the cavity (gunmetal with polished trim) + "7" badge
SLOPE_B = TAN_L - (W0 - WT) / ZT
BACK_UP = Vector((0, SLOPE_B, 1)).normalized()
BACK_N = Vector((0, 1, -SLOPE_B)).normalized()
X_T = Vector((-1, 0, 0))                            # reads left->right when viewed from behind


def cavity_floor_point(x, z):
    return Vector((x, y_front(z) + thick(z), z)) - BACK_N * CAV_DEPTH


MED_W, MED_H = 0.034, 0.0105
med_frame = frame(cavity_floor_point(0.040, 0.0145), X_T, BACK_UP, BACK_N)
mb = bmesh.new()
rr = rounded_rect(MED_W, MED_H, 0.0030)
bot = [mb.verts.new((x, y, -0.0003)) for x, y in rr]
top = [mb.verts.new((x, y, 0.0007)) for x, y in rr]
f_top = mb.faces.new(top)
mb.faces.new(list(reversed(bot)))
for i in range(len(rr)):
    j = (i + 1) % len(rr)
    mb.faces.new((bot[i], bot[j], top[j], top[i]))
bmesh.ops.recalc_face_normals(mb, faces=mb.faces[:])
for f in mb.faces:
    f.material_index = 0
trim = bmesh.ops.inset_region(mb, faces=[f_top], thickness=0.0008, depth=-0.00015, use_even_offset=True)
f_top.material_index = 2
bmesh.ops.transform(mb, matrix=med_frame, verts=mb.verts[:])
append_bm(hb, mb)

cu = bpy.data.curves.new("Num7", 'FONT')
cu.body = "7"
cu.size = 0.0085
cu.extrude = 0.00022
cu.align_x = 'CENTER'
cu.align_y = 'CENTER'
t_obj = bpy.data.objects.new("Num7_tmp", cu)
scene.collection.objects.link(t_obj)
dg = bpy.context.evaluated_depsgraph_get()
dg.update()
me7 = bpy.data.meshes.new_from_object(t_obj.evaluated_get(dg))
bpy.data.objects.remove(t_obj, do_unlink=True)
bpy.data.curves.remove(cu)
me7.transform(med_frame @ Matrix.Translation((-0.0115, 0.0, 0.00055 + 0.00022 - 0.00005)))
for p in me7.polygons:
    p.material_index = 0                            # polished chrome numeral
hb.from_mesh(me7)
bpy.data.meshes.remove(me7)

# Move the head into the club frame (shaft axis = +Z), then add the hosel
bmesh.ops.transform(hb, matrix=HEAD_TO_CLUB, verts=hb.verts[:])
HOSEL = [(0, -0.002), (0.0100, -0.002), (0.0118, 0.003), (0.0116, 0.008), (0.0100, 0.014),
         (0.0086, 0.021), (0.0076, 0.030), (0.0071, 0.042), (0.0068, 0.058), (0.0066, 0.0605), (0, 0.0605)]
hosel = lathe(HOSEL)
assign_by(hosel, lambda r, z: 0)
append_bm(hb, hosel)
head_final = bm_to_mesh(hb, "Club_Head", HEAD_MATS)

# --------------------------------------------------------------------------- ferrule, shaft, grip (club frame)
FERRULE_P = [(0, 0.0600), (0.00672, 0.0600), (0.00676, 0.0618), (0.00664, 0.0640), (0.00630, 0.0700),
             (0.00590, 0.0740), (0.00592, 0.0742), (0.00592, 0.0754), (0.00575, 0.0757),
             (0.00505, 0.0790), (0.00478, 0.0795), (0, 0.0795)]
fb = lathe(FERRULE_P)
assign_by(fb, lambda r, z: 1 if (z < 0.0619 and r > 0.0055) or (0.0741 < z < 0.0755) else 0)
ferrule_me = bm_to_mesh(fb, "Club_Ferrule", [FERRULE, CHROME])

SHAFT_P = [(0, 0.066), (0.00470, 0.066), (0.00478, 0.200)]
r_prev = 0.00478
for z, r_new in zip([0.230, 0.275, 0.320, 0.365, 0.410, 0.455, 0.500, 0.545],
                    [0.00505, 0.00530, 0.00556, 0.00585, 0.00615, 0.00648, 0.00690, 0.00740]):
    SHAFT_P += [(r_prev, z), (r_new, z + 0.0015)]   # step-pattern steel shaft
    r_prev = r_new
SHAFT_P += [(0.00760, 0.600), (0.00762, 0.918), (0, 0.918)]
sb = lathe(SHAFT_P)
assign_by(sb, lambda r, z: 0)
shaft_me = bm_to_mesh(sb, "Club_Shaft", [CHROME])

GRIP_P = [(0, 0.655), (0.0079, 0.655), (0.0092, 0.6565), (0.0101, 0.660), (0.0104, 0.666), (0.0108, 0.700),
          (0.0116, 0.760), (0.0123, 0.820), (0.0129, 0.875), (0.0133, 0.905), (0.0134, 0.915),
          (0.0131, 0.9205), (0.0123, 0.9235), (0.0105, 0.9250), (0.0062, 0.9254), (0.0060, 0.9248),
          (0, 0.9248)]
gb = lathe(GRIP_P)
assign_by(gb, lambda r, z: 1 if (z > 0.9240 and r < 0.0061) else 0)
grip_me = bm_to_mesh(gb, "Club_Grip", [RUBBER, CHROME])

# --------------------------------------------------------------------------- ground the club, build objects
meshes = [head_final, shaft_me, ferrule_me, grip_me]
min_z = min(v.co.z for me in meshes for v in me.vertices)
for me in meshes:
    me.transform(Matrix.Translation((0, 0, -min_z)))
max_z = max(v.co.z for me in meshes for v in me.vertices)


def finish_mesh(me, sharp_deg):
    try:
        me.shade_smooth()
    except AttributeError:
        for p in me.polygons:
            p.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(sharp_deg))
    except Exception as e:
        print("WARN set_sharp_from_angle:", e)


root = bpy.data.objects.new("GolfClub", None)
root.empty_display_type = 'PLAIN_AXES'
root.empty_display_size = 0.08
COL_CLUB.objects.link(root)

parts = {}
for me, sharp in ((head_final, 30), (shaft_me, 60), (ferrule_me, 45), (grip_me, 45)):
    finish_mesh(me, sharp)
    ob = bpy.data.objects.new(me.name, me)
    COL_CLUB.objects.link(ob)
    ob.parent = root
    parts[me.name] = ob

head = parts["Club_Head"]
bev = head.modifiers.new("Bevel", 'BEVEL')
bev.width = 0.00035
bev.segments = 3
bev.limit_method = 'ANGLE'
bev.angle_limit = math.radians(30)
bev.use_clamp_overlap = True
bev.harden_normals = True
wn = head.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
wn.keep_sharp = True


def smart_uv(obj):
    try:
        for o in bpy.context.view_layer.objects:
            o.select_set(False)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.003)
        bpy.ops.object.mode_set(mode='OBJECT')
        return True
    except Exception as e:
        print("WARN UV unwrap failed for", obj.name, e)
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass
        return False


uv_ok = {name: smart_uv(ob) for name, ob in parts.items()}
for o in bpy.context.view_layer.objects:
    o.select_set(False)

# --------------------------------------------------------------------------- presentation: world, lights, cameras
world = bpy.data.worlds.new("Studio")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
wn_tree = world.node_tree
wn_tree.nodes.clear()
hdri_dir = os.path.join(bpy.utils.system_resource('DATAFILES'), "studiolights", "world")
hdri = os.path.join(hdri_dir, "studio.exr")
if not os.path.exists(hdri):
    exrs = sorted(f for f in os.listdir(hdri_dir) if f.endswith(".exr")) if os.path.isdir(hdri_dir) else []
    hdri = os.path.join(hdri_dir, exrs[0]) if exrs else None
out_w = wn_tree.nodes.new('ShaderNodeOutputWorld')
bg_cam = wn_tree.nodes.new('ShaderNodeBackground')
bg_cam.inputs['Color'].default_value = (0.030, 0.032, 0.037, 1.0)
if hdri:
    env = wn_tree.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(hdri)
    env.image.pack()
    bg_light = wn_tree.nodes.new('ShaderNodeBackground')
    bg_light.inputs['Strength'].default_value = 0.8
    lp = wn_tree.nodes.new('ShaderNodeLightPath')
    mix = wn_tree.nodes.new('ShaderNodeMixShader')
    wn_tree.links.new(env.outputs['Color'], bg_light.inputs['Color'])
    wn_tree.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    wn_tree.links.new(bg_light.outputs[0], mix.inputs[1])
    wn_tree.links.new(bg_cam.outputs[0], mix.inputs[2])
    wn_tree.links.new(mix.outputs[0], out_w.inputs['Surface'])
else:
    wn_tree.links.new(bg_cam.outputs[0], out_w.inputs['Surface'])
print("HDRI:", hdri)

CLUB_CENTER = Vector((0.02, 0.0, max_z / 2))


def aim(obj, target, roll_deg=0.0):
    q = (Vector(target) - obj.location).to_track_quat('-Z', 'Y')
    if roll_deg:
        q = q @ Quaternion((0, 0, 1), math.radians(roll_deg))
    obj.rotation_euler = q.to_euler()


def add_area(name, loc, size, energy):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.size = size
    ld.energy = energy
    lo = bpy.data.objects.new(name, ld)
    COL_PRES.objects.link(lo)
    lo.location = loc
    aim(lo, CLUB_CENTER)
    return lo


add_area("Light_Key", (-1.0, -1.6, 1.6), 1.2, 120.0)
add_area("Light_Rim", (1.2, 1.4, 1.2), 1.0, 150.0)
add_area("Light_Fill", (1.6, -0.8, 0.2), 1.5, 40.0)


def add_camera(name, target, direction, dist, lens=85.0, roll=0.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.01
    co = bpy.data.objects.new(name, cd)
    COL_PRES.objects.link(co)
    co.location = Vector(target) + Vector(direction).normalized() * dist
    aim(co, target, roll)
    return co


hv = [v.co for v in head_final.vertices]
head_center = Vector(((min(v.x for v in hv) + max(v.x for v in hv)) / 2,
                      (min(v.y for v in hv) + max(v.y for v in hv)) / 2,
                      (min(v.z for v in hv) + max(v.z for v in hv)) / 2 + 0.01))
cam_hero = add_camera("Cam_Hero", CLUB_CENTER, (0.45, -1.0, 0.18), 2.15, roll=58.0)
cam_front = add_camera("Cam_HeadFront", head_center, (0.30, -1.0, 0.22), 0.38)
cam_back = add_camera("Cam_HeadBack", head_center, (-0.25, 1.0, 0.28), 0.38)

# --------------------------------------------------------------------------- render + viewport settings
scene.render.engine = 'CYCLES'
cy = scene.cycles
cy.samples = SAMPLES
cy.use_denoising = True
try:
    cprefs = bpy.context.preferences.addons['cycles'].preferences
    cprefs.compute_device_type = 'METAL'
    cprefs.get_devices()
    for d in cprefs.devices:
        d.use = True
    cy.device = 'GPU'
    print("CYCLES devices:", [(d.name, d.type) for d in cprefs.devices])
except Exception as e:
    print("WARN GPU setup failed, using CPU:", e)
scene.view_settings.view_transform = 'AgX'
for look in ('AgX - Punchy', 'Punchy'):
    try:
        scene.view_settings.look = look
        break
    except Exception:
        pass
scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_percentage = 100

for scr in bpy.data.screens:
    for area in scr.areas:
        if area.type != 'VIEW_3D':
            continue
        sp = area.spaces.active
        sp.shading.type = 'MATERIAL'
        sp.clip_start = 0.001
        r3d = sp.region_3d
        r3d.view_location = CLUB_CENTER
        r3d.view_distance = 1.5
        r3d.view_perspective = 'PERSP'
        r3d.view_rotation = Euler((math.radians(80), 0, math.radians(22))).to_quaternion()

scene.camera = cam_hero
blend_path = os.path.join(OUT_DIR, "golf_club.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)

# --------------------------------------------------------------------------- report
dg = bpy.context.evaluated_depsgraph_get()
total_tris = 0
for name, ob in parts.items():
    me_eval = ob.evaluated_get(dg).to_mesh()
    me_eval.calc_loop_triangles()
    tris = len(me_eval.loop_triangles)
    total_tris += tris
    ob.evaluated_get(dg).to_mesh_clear()
    print(f"PART {name}: tris={tris} materials={[m.name for m in ob.data.materials]} uv={uv_ok[name]}")
print(f"CLUB height={max_z:.4f} m  total_tris={total_tris}")

if DO_RENDER:
    for cam, fname, rx, ry in ((cam_hero, "golf_club_hero.png", 1600, 1000),
                               (cam_front, "golf_club_head_front.png", 1400, 1000),
                               (cam_back, "golf_club_head_back.png", 1400, 1000)):
        scene.camera = cam
        scene.render.resolution_x, scene.render.resolution_y = rx, ry
        scene.render.filepath = os.path.join(OUT_DIR, "renders", fname)
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath)
    scene.camera = cam_hero
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, compress=True)

print("SAVED", blend_path, os.path.getsize(blend_path), "bytes")
