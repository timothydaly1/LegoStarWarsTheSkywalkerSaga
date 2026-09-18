"""Render preview images of a glTF file with Blender (headless).

    Blender --background --factory-startup --python blender_preview.py -- in.glb out_prefix
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
if "--eevee" in argv:
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    import blender_tss_import
    blender_tss_import.fix_materials()

for spec in [a.split("=", 1)[1] for a in argv if a.startswith("--hide=")]:
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and spec.lower() in o.name.lower():
            bpy.data.objects.remove(o)
for spec in [a.split("=", 1)[1] for a in argv if a.startswith("--only=")]:
    for o in list(bpy.context.scene.objects):
        if o.type == "MESH" and spec.lower() not in o.name.lower():
            bpy.data.objects.remove(o)
objs = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.users_collection and not o.name.startswith("Icosphere")]
depsgraph = bpy.context.evaluated_depsgraph_get()
pts = []
for o in objs:
    ev = o.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    pts += [ev.matrix_world @ v.co for v in mesh.vertices]
    ev.to_mesh_clear()
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
centre, size = (lo + hi) / 2, max((hi - lo).length, 1e-3)

scene = bpy.context.scene
for o in bpy.context.scene.objects:
    if o.name.startswith("Icosphere"):
        o.hide_render = True
scene.render.engine = "BLENDER_EEVEE_NEXT" if "--eevee" in argv else "BLENDER_WORKBENCH"
if "--eevee" in argv:
    world = bpy.data.worlds.new("w")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.85, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    scene.world = world
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = (0.9, 0.2, 0.6)
    scene.collection.objects.link(sun)
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "RANDOM" if "--random" in argv else ("VERTEX" if "--vertex" in argv else "TEXTURE")
scene.render.resolution_x = scene.render.resolution_y = 768
cam_data = bpy.data.cameras.new("cam")
cam_data.lens = 50
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
zoom = float(next((a.split("=")[1] for a in argv if a.startswith("--zoom=")), "1.9"))
for label, az, el in (("front", 180, 10), ("threequarter", 145, 20), ("back", 0, 10)):
    d = size * zoom
    a, e = math.radians(az), math.radians(el)
    # Blender is Z-up after glTF import; NTT models face glTF -Z, which becomes Blender +Y
    cam.location = centre + Vector((d * math.sin(a) * math.cos(e), -d * math.cos(a) * math.cos(e), d * math.sin(e)))
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = f"{out}_{label}.png"
    bpy.ops.render.render(write_still=True)
print("bounds", tuple(lo), tuple(hi))
