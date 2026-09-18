"""Blender helper: import TSS glTF exports and wire vertex colours into materials.

glTF says COLOR_0 multiplies baseColor; Blender's importer ignores it. LEGO brick
colour in this game lives in vertex colours (texture pages are near-neutral), so
after import each material gets Base Color = image * Color Attribute.

Usage inside Blender (Scripting tab) or:
    Blender --python blender_tss_import.py -- file.glb [file2.glb ...]
"""
import sys

import bpy


def fix_materials(objects=None):
    objects = objects or [o for o in bpy.context.scene.objects if o.type == "MESH"]
    done = set()
    for obj in objects:
        if not obj.data.color_attributes:
            continue
        attr_name = obj.data.color_attributes[0].name
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None or not mat.use_nodes or (mat.name, attr_name) in done:
                continue
            done.add((mat.name, attr_name))
            nodes, links = mat.node_tree.nodes, mat.node_tree.links
            bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
            if bsdf is None or any(n.type == "VERTEX_COLOR" for n in nodes):
                continue
            base = bsdf.inputs["Base Color"]
            vcol = nodes.new("ShaderNodeVertexColor")
            vcol.layer_name = attr_name
            vcol.location = (bsdf.location.x - 500, bsdf.location.y - 250)
            mix = nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.location = (bsdf.location.x - 250, bsdf.location.y)
            if base.is_linked:
                src = base.links[0].from_socket
                links.new(src, mix.inputs["A"])
            else:
                mix.inputs["A"].default_value = base.default_value
            links.new(vcol.outputs["Color"], mix.inputs["B"])
            links.new(mix.outputs["Result"], base)
            # vertex alpha drives transparency for alpha-blended materials
            if mat.blend_method != "OPAQUE" or mat.get("alphaMode") == "BLEND":
                alpha = bsdf.inputs["Alpha"]
                if not alpha.is_linked:
                    links.new(vcol.outputs["Alpha"], alpha)


def import_files(paths):
    for p in paths:
        before = set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=p)
        fix_materials([o for o in bpy.context.scene.objects if o not in before and o.type == "MESH"])


if __name__ == "__main__" and "--" in sys.argv:
    import_files(sys.argv[sys.argv.index("--") + 1:])
