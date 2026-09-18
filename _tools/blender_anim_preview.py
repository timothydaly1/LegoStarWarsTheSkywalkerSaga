"""Render frames of each animation in a glTF (headless Blender).

    Blender --background --factory-startup --python blender_anim_preview.py -- in.glb out_prefix [frames...]
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
frames = [int(x) for x in argv[2:]] or [0, 10, 20]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
for o in scene.objects:
    if o.name.startswith("Icosphere"):
        o.hide_render = True
arm = next(o for o in scene.objects if o.type == "ARMATURE")
meshes = [o for o in scene.objects if o.type == "MESH" and not o.name.startswith("Icosphere")]
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "RANDOM"
scene.render.resolution_x = scene.render.resolution_y = 512
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
scene.collection.objects.link(cam)
scene.camera = cam


def bounds():
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in meshes:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts += [ev.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


actions = [a for a in bpy.data.actions]
print("actions", [a.name for a in actions])
for act in actions:
    arm.animation_data_create()
    for tr in list(arm.animation_data.nla_tracks):
        tr.mute = True
    arm.animation_data.action = act
    for f in frames:
        scene.frame_set(f)
        lo, hi = bounds()
        c, size = (lo + hi) / 2, max((hi - lo).length, 1e-3)
        a, e = math.radians(35), math.radians(20)
        cam.location = c + Vector((size * 1.9 * math.sin(a) * math.cos(e), -size * 1.9 * math.cos(a) * math.cos(e), size * 1.9 * math.sin(e)))
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = f"{out}_{act.name}_{f:03d}.png"
        bpy.ops.render.render(write_still=True)
