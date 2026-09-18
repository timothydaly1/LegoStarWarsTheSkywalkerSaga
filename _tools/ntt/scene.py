"""Assemble level scenes (.SCENE_BAKED) into one glTF.

A level is split into several SCENE_BAKED layers (_ART, _GAMEPLAY, _TECH, ...). Each is a
baked entity tree; entities with an ApiRenderModel component place a .MODEL (NuScene2) at the
entity's apiTransformComponent "World NuTransform" (scale xyzw, quaternion xyzw, position xyzw).

Every unique model becomes one glTF mesh (its top-LOD drawable nodes), instanced by one node
per placement. Materials come from the model's .MATERIAL shader graphs (see shadergraph.py).
The exporter mirrors X like the model exporter, so transforms are mirrored to match.
"""
import io
import math
import re
import os
from dataclasses import dataclass

import numpy as np

import json

from . import baked, character as CH, gltf, material as MAT, model as M, scene_model as SM, shadergraph as SG, texture
from .character import resolve_path

TEXTURE_MAX = 1024
# editor/design helpers that are never drawn in game
HELPER_PATHS = ("mapcalibrationframe", "/blockout/", "editoronly", "/debug/")


@dataclass
class Placement:
    entity: str
    model: str          # resource path
    translation: tuple
    rotation: tuple     # quaternion xyzw
    scale: tuple
    layer: str
    colours: str = ""        # .INSTANCE_VERTEX_COLOURS resource baked for this placement (rare)
    kind: str = "model"      # 'model' (ApiRenderModel .MODEL) | 'tt' (nttRenderTTExportObject GSC/GHG)
    special: str = ""
    overrides: dict = None


def _components(e):
    return [c for c in (e.get("Components") or []) if c]


def load_placements(scene_path: str) -> list:
    with open(scene_path, "rb") as f:
        ar = baked.read_archive(f.read())
    objs = baked.Reader(ar).read_olst()
    layer = os.path.splitext(os.path.basename(scene_path))[0]
    out = []

    def walk(e, enabled):
        enabled = enabled and bool(e.get("Enabled", 1))
        comps = _components(e)
        xf = next((c for c in comps if c.get("_class") == "apiTransformComponent"), None)
        for c in comps:
            if c.get("_class") == "ApiRenderModel" and enabled and c.get("Enabled", 1) and c.get("Draw Mesh", 1) \
                    and not c.get("Editor Only Model"):
                res = (c.get("Model Resource") or {}).get("Resource_Path")
                t = (xf or {}).get("World NuTransform")
                if res and isinstance(t, list) and len(t) == 12:
                    vc = ((c.get("Vertex Colours Resource") or {}).get("Resource_Path") or "")
                    out.append(Placement(e.get("Name", ""), res, tuple(t[8:11]), tuple(t[4:8]), tuple(t[0:3]), layer, vc))
            elif c.get("_class") == "nttRenderTTExportObject" and enabled and c.get("Enabled", 1) and "_error" not in c:
                res = (c.get("Model Resource") or {}).get("Resource_Path")
                t = (xf or {}).get("World NuTransform")
                if res and isinstance(t, list) and len(t) == 12:
                    ov = {m["ID"]: m for m in c.get("Material State Overrides") or [] if isinstance(m, dict) and "ID" in m}
                    out.append(Placement(e.get("Name", ""), res, tuple(t[8:11]), tuple(t[4:8]), tuple(t[0:3]), layer,
                                         kind="tt", special=c.get("Special Name", "") or "", overrides=ov))
        for c in comps:
            if c.get("_class") == "apiEntity":
                walk(c, enabled)

    for o in objs:
        walk(o, True)
    return out


# --- materials -----------------------------------------------------------------

def _texture_index(g, res_path):
    cache = g.__dict__.setdefault("_scene_tex", {})
    if res_path in cache:
        return cache[res_path]
    cache[res_path] = None
    f = resolve_path(res_path, ".TEXTURE")
    if not f:
        return None
    try:
        rgba = texture.read_texture(f).to_rgba()
    except Exception:
        return None
    from PIL import Image
    img = Image.fromarray(rgba, "RGBA")
    if max(img.size) > TEXTURE_MAX:
        img.thumbnail((TEXTURE_MAX, TEXTURE_MAX), Image.LANCZOS)
    buf = io.BytesIO()
    if rgba[..., 3].min() >= 250:
        img.convert("RGB").save(buf, "JPEG", quality=90)
        mime = "image/jpeg"
    else:
        img.save(buf, "PNG")
        mime = "image/png"
    data = buf.getvalue()
    while len(g.bin) % 4:
        g.bin.append(0)
    g.gltf["bufferViews"].append({"buffer": 0, "byteOffset": len(g.bin), "byteLength": len(data)})
    g.bin += data
    g.gltf.setdefault("images", []).append({"name": os.path.basename(res_path), "mimeType": mime,
                                            "bufferView": len(g.gltf["bufferViews"]) - 1})
    g.gltf.setdefault("samplers", [{"magFilter": 9729, "minFilter": 9987}])
    g.gltf.setdefault("textures", []).append({"source": len(g.gltf["images"]) - 1, "sampler": 0})
    cache[res_path] = len(g.gltf["textures"]) - 1
    return cache[res_path]


def _srgb_to_linear(c):
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def material_index(g, res_path, slot_name):
    """-> (glTF material index or None to skip, uses vertex colour)"""
    cache = g.__dict__.setdefault("_scene_mats", {})
    key = (res_path or "").lower()
    if key in cache:
        return cache[key]
    low = key.rsplit("/", 1)[-1]
    if any(w in low for w in ("shadow", "occluder", "z_only", "depthonly")):
        cache[key] = (None, False)
        return cache[key]
    sm = None
    f = resolve_path(res_path) if res_path else None
    if f:
        try:
            sm = SG.read_material(f)
        except Exception:
            sm = None
    gm = {"name": (sm.name if sm else slot_name) or low,
          "pbrMetallicRoughness": {"metallicFactor": 0.0, "roughnessFactor": 0.6}}
    vc = True
    if sm:
        a = sm.albedo
        vc = a.vertex_color
        if a.color and len(a.color) >= 3:
            gm["pbrMetallicRoughness"]["baseColorFactor"] = [*_srgb_to_linear(a.color[:3]), 1.0]
        if a.texture:
            ti = _texture_index(g, a.texture)
            if ti is not None:
                gm["pbrMetallicRoughness"]["baseColorTexture"] = {"index": ti, "texCoord": min(a.texcoord, 1)}
        if sm.roughness.color and len(sm.roughness.color) == 1:
            gm["pbrMetallicRoughness"]["roughnessFactor"] = float(min(max(sm.roughness.color[0], 0), 1))
        if sm.metalness.color and len(sm.metalness.color) == 1:
            gm["pbrMetallicRoughness"]["metallicFactor"] = float(min(max(sm.metalness.color[0], 0), 1))
        if sm.emissive.texture:
            ti = _texture_index(g, sm.emissive.texture)
            if ti is not None:
                gm["emissiveTexture"] = {"index": ti}
                gm["emissiveFactor"] = [1.0, 1.0, 1.0]
        elif sm.emissive.color and len(sm.emissive.color) >= 3 and max(sm.emissive.color[:3]) > 0:
            gm["emissiveFactor"] = [float(min(x, 1)) for x in sm.emissive.color[:3]]
        if sm.alpha_linked:
            al = sm.alpha
            if al.texture:
                gm["alphaMode"] = "MASK"
                gm["alphaCutoff"] = 0.5
            elif al.color and len(al.color) == 1 and al.color[0] < 0.99:
                gm["alphaMode"] = "BLEND"
                gm["pbrMetallicRoughness"].setdefault("baseColorFactor", [1.0, 1.0, 1.0, 1.0])[3] = float(max(al.color[0], 0.05))
        gm["extras"] = {"material": res_path}
    g.gltf.setdefault("materials", []).append(gm)
    cache[key] = (len(g.gltf["materials"]) - 1, vc)
    return cache[key]


# --- models --------------------------------------------------------------------

def model_mesh(g, res_path, stats, colours_path=""):
    cache = g.__dict__.setdefault("_scene_meshes", {})
    key = (res_path.lower(), colours_path.lower())
    if key in cache:
        return cache[key]
    cache[key] = None
    f = resolve_path(res_path)
    if not f:
        stats["missing"] = stats.get("missing", 0) + 1
        stats.setdefault("missing_paths", []).append(res_path)
        return None
    try:
        sm = SM.read_scene_model(f)
    except Exception as ex:
        stats["failed"] = stats.get("failed", 0) + 1
        stats.setdefault("errors", []).append(f"{res_path}: {ex}")
        return None
    colours = []
    if colours_path:
        from . import instance_colours as IC
        f2 = resolve_path(colours_path)
        try:
            colours = IC.read_instance_colours(f2) if f2 else []
        except Exception:
            colours = []
        if colours and not IC.matches(colours, sm.parts):
            stats["colour_mismatch"] = stats.get("colour_mismatch", 0) + 1
            colours = []
    prims = []
    for node in sm.visible_nodes():
        ci = node.models[0]
        if not 0 <= ci < len(sm.clip_objects):
            continue
        for item in sm.clip_objects[ci]:
            if item.mesh >= len(sm.parts):
                continue
            path, slot = sm.materials[item.material] if item.material < len(sm.materials) else (None, "")
            mi, vc = material_index(g, path, slot)
            if mi is None:
                continue
            xform = None
            if 0 < item.transform < len(sm.transforms):
                xform = sm.transforms[item.transform]
            if node.transform is not None and not np.allclose(node.transform, np.eye(4)):
                xform = node.transform if xform is None else xform @ node.transform
            mp = sm.parts[item.mesh]
            prim = gltf.part_primitive(g, mp, None, None, xform)
            if prim is None:
                continue
            if item.mesh < len(colours):           # per-instance baked lighting replaces the model's colours
                c = colours[item.mesh][mp.ib_base:mp.ib_base + mp.vb_used]
                if len(c) == mp.vb_used:
                    prim["attributes"]["COLOR_0"] = g.add_accessor(np.ascontiguousarray(c), gltf.ARRAY_BUFFER,
                                                                   normalized=True)
                    vc = True
            if not vc:
                prim["attributes"].pop("COLOR_0", None)
            prim["material"] = mi
            prims.append(prim)
    if not prims:
        return None
    g.gltf["meshes"].append(gltf.mesh_with_weights(g, os.path.splitext(os.path.basename(res_path))[0], prims))
    cache[key] = len(g.gltf["meshes"]) - 1
    stats["models"] = stats.get("models", 0) + 1
    return cache[key]


SKIP_SPECIAL_WORDS = ("shadow", "zocc", "occluder", "collision", "collide")


def _override_signature(ov):
    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in sorted(o.items(), key=lambda kv: str(kv[0])) if not str(k).startswith("_") and k != "Guid"}
        if isinstance(o, list):
            return [clean(v) for v in o]
        if isinstance(o, bytes):
            return o.hex()
        return o
    return json.dumps(clean(ov or {}), sort_keys=True, default=str)


def tt_mesh(g, p: Placement, stats):
    """GSC/GHG prop through a TT export object: one mesh for the chosen special(s) with overrides."""
    sig = _override_signature(p.overrides)
    cache = g.__dict__.setdefault("_scene_tt", {})
    key = (p.model.lower(), p.special.lower(), sig)
    if key in cache:
        return cache[key]
    cache[key] = None
    f = resolve_path(p.model)
    if not f or not f.upper().endswith((".GSC", ".GHG")):
        stats["missing"] = stats.get("missing", 0) + 1
        stats.setdefault("missing_paths", []).append(p.model)
        return None
    models = g.__dict__.setdefault("_scene_tt_models", {})
    if f not in models:
        try:
            from .resource import read_resource
            models[f] = (M.read_model(f), MAT.read_materials(read_resource(f).body))
        except Exception as ex:
            models[f] = None
            stats["failed"] = stats.get("failed", 0) + 1
            stats.setdefault("errors", []).append(f"{p.model}: {ex}")
    if models[f] is None:
        return None
    mdl, mats = models[f]
    want = p.special.lower()
    if not want or want.startswith("["):
        specials = [sp for sp in mdl.specials
                    if not sp.name.lower().startswith("loc_")
                    and not any(w in sp.name.lower() for w in gltf.BREAKUP_WORDS + SKIP_SPECIAL_WORDS)
                    and not re.search(r"_lod[1-9]$", sp.name.lower())]
    else:
        specials = [sp for sp in mdl.specials if sp.name.lower() == want]
    part = CH.RenderPart(f"{os.path.basename(f)}#{len(cache)}", p.model, p.special, p.overrides or {}, set(),
                         path=f)
    prims = []
    for sp in specials:
        if not 0 <= sp.clip_object < len(mdl.clip_objects):
            continue
        xform = sp.matrix if np.any(sp.matrix) and not np.allclose(sp.matrix, np.eye(4)) else None
        for item in mdl.clip_objects[sp.clip_object]:
            if item.mesh >= len(mdl.parts):
                continue
            mat = mats[item.material] if item.material < len(mats) else None
            mp = mdl.parts[item.mesh]
            if (mat and (mat.is_shadow_only or CH._is_occluder(mat))) or (not mats and gltf.is_proxy(mp)):
                continue
            prim = gltf.part_primitive(g, mp, None, None, xform)
            if prim is None:
                continue
            ov = part.overrides.get(mat.fields.get("special_id")) if mat else None
            if ov:
                prim["attributes"].pop("COLOR_0", None)
            mi = CH._override_material(g, part, mat, (f, sig, item.material))
            if mi is None:
                continue
            prim["material"] = mi
            prims.append(prim)
    if not prims:
        return None
    g.gltf["meshes"].append(gltf.mesh_with_weights(g, f"{os.path.splitext(os.path.basename(f))[0]}:{p.special}", prims))
    cache[key] = len(g.gltf["meshes"]) - 1
    stats["props"] = stats.get("props", 0) + 1
    return cache[key]


def scene_to_glb(scene_paths, name_filter=None) -> tuple:
    g = gltf.GlbBuilder()
    stats = {}
    layers = {}
    for sp in scene_paths:
        try:
            placements = load_placements(sp)
        except Exception as ex:
            stats.setdefault("errors", []).append(f"{sp}: {ex}")
            continue
        for p in placements:
            if any(h in p.model.lower() for h in HELPER_PATHS):
                continue
            if name_filter and name_filter.lower() not in p.model.lower():
                continue
            mesh = model_mesh(g, p.model, stats, p.colours) if p.kind == "model" else tt_mesh(g, p, stats)
            if mesh is None:
                continue
            if p.layer not in layers:
                layers[p.layer] = g.add_node({"name": p.layer, "children": []}, root=True)
            x, y, z = p.translation
            qx, qy, qz, qw = p.rotation
            qn = math.sqrt(qx * qx + qy * qy + qz * qz + qw * qw) or 1.0
            node = {"name": p.entity, "mesh": mesh,
                    "translation": [-x, y, z],
                    "rotation": [qx / qn, -qy / qn, -qz / qn, qw / qn]}
            if any(abs(s - 1) > 1e-5 for s in p.scale):
                node["scale"] = list(p.scale)
            idx = g.add_node(node)
            g.gltf["nodes"][layers[p.layer]]["children"].append(idx)
            stats["instances"] = stats.get("instances", 0) + 1
    return g.to_glb(), stats
