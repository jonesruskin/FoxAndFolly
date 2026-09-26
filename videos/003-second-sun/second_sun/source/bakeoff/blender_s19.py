"""Bake-off pipeline A: S19 'second sunrise' at test quality in Blender (headless bpy).
Usage: blender -b -P blender_s19.py -- <engine CYCLES|BLENDER_EEVEE> <out.png> <samples>"""
import bpy, bmesh, sys, math, time
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
engine, out, samples = argv[0], argv[1], int(argv[2])
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def mat(name, col, rough=0.8, emit=None, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = 8
    return m

# ground with ferny noise
bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0))
g = bpy.context.object; g.data.materials.append(mat("ground", (0.12, 0.14, 0.06)))
# lake
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 25, 0.05))
lake = bpy.context.object; lake.data.materials.append(mat("water", (0.05, 0.12, 0.14), rough=0.05))
# ridge with a saddle notch
bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=4, size=1, location=(0, 90, 0))
r = bpy.context.object; r.scale = (220, 10, 1)
bm = bmesh.new(); bm.from_mesh(r.data)
for v in bm.verts:
    x = v.co.x * 220
    h = 9 + 4 * math.sin(x * 0.05) + 2 * math.sin(x * 0.17)
    h -= 7 * math.exp(-((x - 30) / 6) ** 2)  # the Saddle
    v.co.z = h * (0.5 - v.co.y) * 1.0
bm.to_mesh(r.data); r.data.materials.append(mat("ridge", (0.06, 0.06, 0.07)))
# skin-modifier triceratops (edge skeleton -> skin -> subsurf)
verts = [(-4, 0, 1.4), (-2.5, 0, 1.9), (0, 0, 2.2), (2, 0, 2.1), (3.2, 0, 1.9), (4.2, 0, 1.9),
         (-1.2, 0.6, 1.5), (-1.2, 0.8, 0.0), (-1.2, -0.6, 1.5), (-1.2, -0.8, 0.0),
         (2.0, 0.6, 1.4), (2.0, 0.7, 0.0), (2.0, -0.6, 1.4), (2.0, -0.7, 0.0), (5.2, 0, 1.4)]
edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (2, 6), (6, 7), (2, 8), (8, 9), (3, 10), (10, 11),
         (3, 12), (12, 13), (5, 14)]
me = bpy.data.meshes.new("tri"); me.from_pydata(verts, edges, []); ob = bpy.data.objects.new("tri", me)
sc.collection.objects.link(ob)
ob.modifiers.new("skin", "SKIN"); ob.modifiers.new("sub", "SUBSURF").levels = 2
radii = [0.15, 0.6, 1.2, 1.25, 0.9, 0.7, 0.45, 0.35, 0.45, 0.35, 0.4, 0.33, 0.4, 0.33, 0.35]
for i, sv in enumerate(ob.data.skin_vertices[0].data):
    sv.radius = (radii[i], radii[i])
ob.data.materials.append(mat("tri", (0.35, 0.28, 0.24)))
ob.location = (-3, 8, 0)
# frill disc
bpy.ops.mesh.primitive_cylinder_add(radius=1.6, depth=0.15, location=(1.6, 8, 3.2), rotation=(0, math.radians(70), 0))
bpy.context.object.data.materials.append(mat("frill", (0.6, 0.42, 0.40)))
# split tree
for sgn in (-1, 1):
    bpy.ops.mesh.primitive_cone_add(radius1=0.6, radius2=0.1, depth=14, location=(-12 + sgn * 1.2, 12, 7),
                                    rotation=(0, sgn * 0.18, 0))
    bpy.context.object.data.materials.append(mat("bark", (0.10, 0.07, 0.05)))
# the second sun: emissive sphere behind the saddle + sun lamp from the south
bpy.ops.mesh.primitive_uv_sphere_add(radius=6, location=(30, 140, 6))
bpy.context.object.data.materials.append(mat("flash", (1, 1, 1), emit=(1.0, 0.9, 0.7)))
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(-80), 0, math.radians(180)))
bpy.context.object.data.energy = 6; bpy.context.object.data.color = (1.0, 0.9, 0.75)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.35, 0.3, 0.28, 1)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
cam.location = (0, -18, 3.2); cam.rotation_euler = (math.radians(86), 0, 0); sc.camera = cam
sc.render.engine = engine
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 50
if engine == "CYCLES":
    sc.cycles.samples = samples; sc.cycles.use_denoising = False; sc.cycles.device = "CPU"
else:
    sc.eevee.taa_render_samples = samples; sc.eevee.use_bloom = True
sc.render.filepath = out
t = time.time(); bpy.ops.render.render(write_still=True); print("RENDER_SECONDS", time.time() - t)
