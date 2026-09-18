"""Render close-ups of a character's head over animation frames (headless Blender, EEVEE).

    Blender --background --factory-startup --python blender_face_preview.py -- in.glb out_prefix ACTION f1 f2 ...
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
src, out, action = argv[0], argv[1], argv[2]
frames = [int(x) for x in argv[3:]] or [0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import blender_tss_import
blender_tss_import.fix_materials()
scene = bpy.context.scene
for o in scene.objects:
    if o.name.startswith("Icosphere"):
        o.hide_render = True
arms = [o for o in scene.objects if o.type == "ARMATURE"]
for arm in arms:
    ad = arm.animation_data or arm.animation_data_create()
    for tr in ad.nla_tracks:
        tr.mute = True
    act = next((a for a in bpy.data.actions if a.name.startswith(action) and arm.name in a.name), None) \
        or next((a for a in bpy.data.actions if a.name.startswith(action)), None)
    ad.action = act
    print("armature", arm.name, "action", act.name if act else None)
scene.render.engine = "BLENDER_EEVEE_NEXT"
world = bpy.data.worlds.new("w")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.85, 1)
scene.world = world
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 3.0
sun.rotation_euler = (0.9, 0.2, 2.6)
scene.collection.objects.link(sun)
scene.render.resolution_x = scene.render.resolution_y = 384
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
scene.collection.objects.link(cam)
scene.camera = cam
arm = arms[0]
head = next(b for b in arm.pose.bones if b.name == "Head")
for f in frames:
    scene.frame_set(f)
    c = arm.matrix_world @ (head.matrix @ Vector((0, 0.05, 0, 1))).to_3d() if False else arm.matrix_world @ head.head
    c = c + Vector((0, 0, 0.05))
    cam.location = c + Vector((0, 0.35, 0.02))          # NTT characters face +Y in Blender
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = f"{out}_{f:03d}.png"
    bpy.ops.render.render(write_still=True)
