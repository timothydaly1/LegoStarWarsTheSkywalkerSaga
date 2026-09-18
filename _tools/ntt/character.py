"""Assemble a character from its .PREFAB_BAKED into one glTF.

A character prefab is an entity tree. Render entities carry an
nttRenderTTExportObject (model resource + per-material 'Material State
Overrides' + per-layer 'Layer State Overrides'); attachments carry
AttachToSkeletonComponent (joint name) or AttachToLocatorComponent (skeleton
point-of-interest name).

Material overrides are keyed by the model material's `special_id`. Each has 4
layers: diffuse_N texture handles, colour_tint_N (applied when
colour_tint_enabled_N), and layer 3 is weathering (ignored). Layer 0 is the
base plastic colour (or a decal texture on face meshes); layers 1-2 are prints
alpha-blended on top and use the second UV set.
"""
import io
import os
from dataclasses import dataclass, field

import numpy as np

from . import baked, dds, gltf, material as MAT, model as M, texture

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PRINT_TEXCOORD = 0
TEMPLATE_NAMES = ("lego_white", "alpha.", "dummy_", "plastic_roughness")   # basename prefixes


def is_template(path):
    base = path.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return base.startswith(TEMPLATE_NAMES)

ITEM_LOCATOR = "RightHand_Locator"

_file_index = None


def resolve_path(res_path: str, ext_default: str = "") -> str | None:
    """Engine resource path (any case, no _DX11) -> file on disk."""
    global _file_index
    if not res_path:
        return None
    if _file_index is None:
        _file_index = {}
        for d, dirs, files in os.walk(ROOT):
            dirs[:] = [x for x in dirs if not x.startswith(("_", "."))]
            for f in files:
                _file_index[os.path.relpath(os.path.join(d, f), ROOT).upper()] = os.path.join(d, f)
    p = res_path.replace("\\", "/").strip("/").upper()
    stem, ext = os.path.splitext(p)
    for cand in (p, f"{stem}_DX11{ext}", stem + ext_default, f"{stem}_DX11{ext_default}"):
        if cand in _overlay_index:
            return _overlay_index[cand]
        if cand in _file_index:
            return _file_index[cand]
    return None


_overlay_index = {}


def set_overlay(mod_dir: str):
    """Resolve resources from `mod_dir` (mirroring game paths) before the game folder."""
    _overlay_index.clear()
    _tex_cache.clear()
    for d, _, files in os.walk(mod_dir):
        for f in files:
            _overlay_index[os.path.relpath(os.path.join(d, f), mod_dir).upper()] = os.path.join(d, f)


@dataclass
class RenderPart:
    entity: str
    model: str                     # resource path
    special: str
    overrides: dict                # special_id -> override dict
    hidden_layers: set
    attach_kind: str | None = None  # 'joint' | 'locator' | None
    attach_name: str = ""
    is_root: bool = False
    path: str = ""                 # resolved model file
    enabled: bool = True


def _components(entity):
    return [c for c in (entity.get("Components") or []) if c]


def load_prefab(path: str) -> list:
    with open(path, "rb") as f:
        ar = baked.read_archive(f.read())
    objs = baked.Reader(ar).read_olst()
    parts = []

    def walk(entity, attached, depth, enabled=True):
        enabled = enabled and bool(entity.get("Enabled", 1))
        comps = _components(entity)
        if depth > 0 and entity.get("Name", "").lower() == "items" and attached is None:
            # held items are equipped by gameplay code; mount them in the right hand
            attached = ("locator", ITEM_LOCATOR)
        tt = next((c for c in comps if c.get("_class") == "nttRenderTTExportObject"), None)
        att = next((c for c in comps if c.get("_class") in ("AttachToSkeletonComponent",
                                                               "AttachToLocatorComponent")), None)
        if att is not None:
            attached = ("joint", att.get("Joint", "")) if att["_class"] == "AttachToSkeletonComponent" \
                else ("locator", att.get("Locator", ""))
        if tt is not None and "_error" not in tt:
            ov = {m["ID"]: m for m in tt.get("Material State Overrides") or [] if isinstance(m, dict)}
            hidden = {l["ID"] for l in tt.get("Layer State Overrides") or [] if isinstance(l, dict) and not l.get("Visible", 1)}
            parts.append(RenderPart(entity.get("Name", ""), tt["Model Resource"].get("Resource_Path", ""),
                                    tt.get("Special Name", ""), ov, hidden,
                                    attached[0] if attached else None, attached[1] if attached else "",
                                    is_root=depth == 0, enabled=enabled and bool(tt.get("Enabled", 1))))
        for c in comps:
            if c.get("_class") == "apiEntity":
                walk(c, attached, depth + 1, enabled)

    for o in objs:
        walk(o, None, 0)
    return parts


# --- material baking ---------------------------------------------------------

_tex_cache = {}


def load_rgba(res_path):
    if res_path in _tex_cache:
        return _tex_cache[res_path]
    img = None
    f = resolve_path(res_path, ".TEXTURE")
    if f:
        try:
            img = texture.read_texture(f).to_rgba()
        except Exception:
            img = None
    _tex_cache[res_path] = img
    return img


def _tint(ov, n):
    if ov and ov.get(f"colour_tint_enabled_{n}"):
        return np.array(ov[f"colour_tint_{n}"], np.float32)
    return np.ones(3, np.float32)


def _layer_texture(ov, n):
    if not ov:
        return None
    h = ov.get(f"diffuse_{n}")
    p = h.get("Resource_Path") if isinstance(h, dict) else None
    if not p or is_template(p):
        return None
    return p


_nxg_cache = {}


def model_texture_rgba(model_path, tid):
    """(name, RGBA) of entry `tid` of a model's own .NXG_TEXTURES table (external .TEX pages resolved)."""
    if tid is None:
        return "", None
    if model_path not in _nxg_cache:
        nxg = os.path.splitext(model_path)[0] + ".NXG_TEXTURES"
        try:
            _nxg_cache[model_path] = texture.read_nxg_textures(nxg) if os.path.exists(nxg) else []
        except Exception:
            _nxg_cache[model_path] = []
    table = _nxg_cache[model_path]
    if not 0 <= tid < len(table):
        return "", None
    e = table[tid]
    data = e.dds
    if e.external:
        f = resolve_path(e.name)
        data = open(f, "rb").read() if f else None
    if not data:
        return e.name, None
    try:
        info = dds.parse_dds_header(data)
        return e.name, dds.decode_rgba(info.fmt, data[info.header_size:], info.width, info.height)
    except Exception:
        return e.name, None


def bake_override(ov, fallback=None):
    """-> dict(color=(r,g,b), image=RGBA uint8 or None, texcoord=int, blend=bool, invisible=bool)

    fallback: the material's own layer-0 texture (RGBA), used when the override supplies none."""
    base_tint = _tint(ov, 0)
    base_tex = _layer_texture(ov, 0)
    prints = [(p, _tint(ov, n)) for n in (1, 2) if (p := _layer_texture(ov, n))]
    if not prints and (base_tex or fallback is not None):
        img = load_rgba(base_tex) if base_tex else fallback
        if img is None and fallback is not None:
            img = fallback
        if img is not None and img[..., 3].max() < 8:
            return {"invisible": True}              # empty overlay slot (template alpha texture)
        if img is None:
            return {"color": base_tint, "image": None, "texcoord": 0, "blend": False}
        out = img.astype(np.float32)
        out[..., :3] *= base_tint
        return {"color": np.ones(3), "image": out.clip(0, 255).astype(np.uint8), "texcoord": 0,
                "blend": bool((img[..., 3] < 250).any())}
    if not prints:
        return {"color": base_tint, "image": None, "texcoord": 0, "blend": False}
    layers = [(load_rgba(p), t) for p, t in prints]
    layers = [(im, t) for im, t in layers if im is not None]
    if not layers:
        return {"color": base_tint, "image": None, "texcoord": 0, "blend": False}
    h, w = max(im.shape[0] for im, _ in layers), max(im.shape[1] for im, _ in layers)
    out = np.empty((h, w, 3), np.float32)
    out[:] = base_tint * 255.0
    from PIL import Image
    for im, t in layers:
        if im.shape[:2] != (h, w):
            im = np.array(Image.fromarray(im).resize((w, h), Image.LANCZOS))
        a = im[..., 3:4].astype(np.float32) / 255.0
        out = out * (1 - a) + im[..., :3].astype(np.float32) * t * a
    rgba = np.dstack([out.clip(0, 255).astype(np.uint8), np.full((h, w), 255, np.uint8)])
    return {"color": np.ones(3), "image": rgba, "texcoord": PRINT_TEXCOORD, "blend": False}


def _embed_rgba(g, rgba, name):
    from PIL import Image
    img = Image.fromarray(rgba, "RGBA")
    buf = io.BytesIO()
    if rgba[..., 3].min() == 255:
        img.convert("RGB").save(buf, "JPEG", quality=92)
        mime = "image/jpeg"
    else:
        img.save(buf, "PNG")
        mime = "image/png"
    data = buf.getvalue()
    while len(g.bin) % 4:
        g.bin.append(0)
    g.gltf["bufferViews"].append({"buffer": 0, "byteOffset": len(g.bin), "byteLength": len(data)})
    g.bin += data
    g.gltf.setdefault("images", []).append({"name": name, "mimeType": mime, "bufferView": len(g.gltf["bufferViews"]) - 1})
    g.gltf.setdefault("samplers", [{"magFilter": 9729, "minFilter": 9987}])
    g.gltf.setdefault("textures", []).append({"source": len(g.gltf["images"]) - 1, "sampler": 0})
    return len(g.gltf["textures"]) - 1


def _srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


# mouth interior: only visible when the face rig opens the mouth (collapsed at rest, pokes through the lips)
MOUTH_INTERIOR = ("tongue_mat", "teeth_mat", "mouthback_mat")


NORMAL_MAPS = True
SURFACE_MAX = 1024


def _slot_texture(ov, kind, n):
    h = (ov or {}).get(f"{kind}_{n}")
    p = h.get("Resource_Path") if isinstance(h, dict) else None
    return p if p and not is_template(p) else None


def _embed_cached(g, key, make):
    cache = g.__dict__.setdefault("_char_surface", {})
    if key not in cache:
        rgba = make()
        cache[key] = None if rgba is None else _embed_rgba(g, rgba, key.rsplit("/", 1)[-1])
    return cache[key]


def _shrink(rgba):
    if rgba is None or max(rgba.shape[:2]) <= SURFACE_MAX:
        return rgba
    from PIL import Image
    img = Image.fromarray(rgba, "RGBA")
    img.thumbnail((SURFACE_MAX, SURFACE_MAX), Image.LANCZOS)
    return np.array(img)


def _add_surface_maps(g, gm, ov):
    """normal_N (tangent space, DirectX green) -> normalTexture; specular_N 'BRDF' (G = roughness)
    -> metallicRoughnessTexture. The print layer (1) wins over the base plastic layer (0)."""
    nrm = _slot_texture(ov, "normal", 1) or _slot_texture(ov, "normal", 0)
    if nrm:
        def make_normal():
            a = load_rgba(nrm)
            if a is None:
                return None
            a = _shrink(a).copy()
            a[..., 1] = 255 - a[..., 1]                 # DirectX -> OpenGL/glTF green
            a[..., 3] = 255
            return a
        ti = _embed_cached(g, "nrm:" + nrm, make_normal)
        if ti is not None:
            gm["normalTexture"] = {"index": ti, "texCoord": 0}
    brdf = _slot_texture(ov, "specular", 1) or _slot_texture(ov, "specular", 0)
    if brdf:
        def make_rough():
            a = load_rgba(brdf)
            if a is None:
                return None
            a = _shrink(a)
            out = np.zeros_like(a)
            out[..., 1] = a[..., 1]                     # roughness
            out[..., 3] = 255                           # metalness (B) stays 0
            out[..., 0] = 255
            return out
        ti = _embed_cached(g, "rough:" + brdf, make_rough)
        if ti is not None:
            gm["pbrMetallicRoughness"]["metallicRoughnessTexture"] = {"index": ti, "texCoord": 0}
            gm["pbrMetallicRoughness"]["roughnessFactor"] = 1.0


def _override_material(g, part: RenderPart, mat: MAT.Material, key):
    cache = g.__dict__.setdefault("_char_mats", {})
    if key in cache:
        return cache[key]
    ov = part.overrides.get(mat.fields.get("special_id")) if mat else None
    fallback, invisible = None, bool(mat and mat.name.lower() in MOUTH_INTERIOR)
    h = (ov or {}).get("diffuse_0")
    if isinstance(h, dict) and "/alpha." in (h.get("Resource_Path") or "").lower():
        invisible = True                                # overlay slot explicitly emptied
    if invisible:
        pass
    elif mat and mat.diffuse[0] is not None and not _layer_texture(ov, 0):
        name, rgba = model_texture_rgba(part.path, mat.diffuse[0])
        if "/alpha." in name.lower():
            invisible = True
        elif not is_template(name):
            fallback = rgba
    b = {"invisible": True} if invisible else bake_override(ov, fallback)
    if b.get("invisible"):
        cache[key] = None
        return None
    lin = _srgb_to_linear(np.asarray(b["color"], np.float64))      # tints are authored in sRGB
    gm = {"name": f"{part.entity}:{mat.name if mat else 'material'}",
          "pbrMetallicRoughness": {"metallicFactor": 0.0, "roughnessFactor": 0.45,
                                   "baseColorFactor": [float(lin[0]), float(lin[1]), float(lin[2]), 1.0]}}
    if b["image"] is not None:
        ti = _embed_rgba(g, b["image"], gm["name"])
        gm["pbrMetallicRoughness"]["baseColorTexture"] = {"index": ti, "texCoord": b["texcoord"]}
    if b["blend"]:
        gm["alphaMode"] = "MASK"          # crisp decals; BLEND sorts badly in real-time renderers
        gm["alphaCutoff"] = 0.5
    if NORMAL_MAPS and ov:
        _add_surface_maps(g, gm, ov)
    g.gltf.setdefault("materials", []).append(gm)
    cache[key] = len(g.gltf["materials"]) - 1
    return cache[key]


# --- export ------------------------------------------------------------------

def _poi(skel, name):
    for n, mtx, parent in skel.pois:
        if n.lower() == name.lower():
            return mtx, parent
    return None


def _joint_index(skel, name):
    for i, j in enumerate(skel.joints):
        if j.name.lower() == name.lower():
            return i
    return None


def _uv1_from_uv0(part: M.MeshPart):
    """Second UV set: UV1 attribute if present, else the zw of UV0."""
    got = part.attribute(M.UV1)
    if got is not None:
        return got[0][:, :2]
    got = part.attribute(M.UV0)
    if got is not None and got[0].shape[1] >= 4:
        return got[0][:, 2:4]
    return None


def _is_occluder(mat: MAT.Material):
    """Depth-only helpers (ZHEAD, Occulder*_MAT): no texture slots, no UV set, no special id."""
    return (mat.fields.get("m_UVSet") == MAT.NO_TID and not mat.fields.get("special_id")
            and all(t is None for t in mat.diffuse))


RIGGED_ATTACHMENTS = True   # attachments with their own skeleton get their own skin under the attach joint
DECAL_PUSH = 1.012        # face decals sit exactly on the head surface; scale them out to avoid z-fighting


def _special_bounds(mdl, name):
    sp = next((s for s in mdl.specials if s.name.lower() == name.lower()), None)
    if sp is None or not 0 <= sp.clip_object < len(mdl.clip_objects):
        return None
    pts = []
    for it in mdl.clip_objects[sp.clip_object]:
        if it.mesh < len(mdl.parts):
            mp = mdl.parts[it.mesh]
            got = mp.attribute(M.POSITION)
            if got is not None:
                pts.append(got[0][mp.ib_base:mp.ib_base + mp.vb_used, :3])
    if not pts:
        return None
    v = np.concatenate(pts)
    return v.min(0), v.max(0)


def _add_part_meshes(g, mdl, mats, part: RenderPart, skin, num_joints, specials, rigid_joint=None, xform=None):
    count = 0
    for special in specials:
        items = mdl.clip_objects[special.clip_object] if 0 <= special.clip_object < len(mdl.clip_objects) else []
        prims = []
        for item in items:
            if item.mesh >= len(mdl.parts):
                continue
            mp = mdl.parts[item.mesh]
            mat = mats[item.material] if item.material < len(mats) else None
            if (mat and (mat.is_shadow_only or _is_occluder(mat))) or (not mats and gltf.is_proxy(mp)):
                continue
            prim = gltf.part_primitive(g, mp, num_joints, rigid_joint, xform)
            if prim is None:
                continue
            # character parts carry all-white vertex colours; colour comes from the override tints
            prim["attributes"].pop("COLOR_0", None)
            uv1 = _uv1_from_uv0(mp)
            if uv1 is not None:
                lo, hi = mp.ib_base, mp.ib_base + mp.vb_used
                prim["attributes"]["TEXCOORD_1"] = g.add_accessor(np.ascontiguousarray(uv1[lo:hi], np.float32),
                                                                  gltf.ARRAY_BUFFER)
            mi = _override_material(g, part, mat, (part.entity, item.material))
            if mi is None:
                continue
            prim["material"] = mi
            prims.append(prim)
        if prims:
            g.gltf["meshes"].append(gltf.mesh_with_weights(g, f"{part.entity}:{special.name}", prims))
            node = {"name": f"{part.entity}:{special.name}", "mesh": len(g.gltf["meshes"]) - 1}
            if skin is not None:
                node["skin"] = skin
            g.add_node(node, root=True)
            count += 1
    return count


def _lod0_specials(mdl, hidden_layers=(), breakups=False):
    """Specials used by skeleton 0's layers (visible layers only) -> [(special, meta)]"""
    skel = mdl.skeletons[0]
    layer_of = {}
    for li, layer in enumerate(skel.layers):
        for k in range(layer.meta_index, layer.meta_index + layer.num_rigids + layer.num_skins):
            layer_of[k] = li
    out = []
    for k, meta in enumerate(skel.layer_meta):
        if layer_of.get(k) in hidden_layers or meta.special >= len(mdl.specials):
            continue
        sp = mdl.specials[meta.special]
        lname = skel.layers[layer_of[k]].name if k in layer_of else ""
        if not breakups and any(w in (sp.name + lname).lower() for w in gltf.BREAKUP_WORDS):
            continue
        if sp.name.lower().startswith("zhead"):              # depth pre-pass copy of the head
            continue
        out.append((sp, meta))
    return out


def _add_attachment_rig(g, sub: M.Skeleton, parent_node: int, attach_local: np.ndarray,
                        name: str, pre: np.ndarray | None = None):
    """Joint nodes for an attachment's own skeleton (face, cape, skinned hair ...), parented under the
    body joint it attaches to. attach_local: row-vector transform from the attachment's model space to the
    body joint's space.
    pre: extra model-space transform applied at the rig root only (not in the bind), e.g. decal push."""
    base = len(g.gltf["nodes"])
    for i, jt in enumerate(sub.joints):
        m = sub.local_bind[i] if i < len(sub.local_bind) else np.eye(4, dtype=np.float32)
        if jt.parent < 0:
            m = m @ attach_local if pre is None else m @ pre @ attach_local
        g.add_node({"name": f"{name}:{jt.name}", "matrix": gltf._mirror_matrix(m)})
    for i, jt in enumerate(sub.joints):
        parent = parent_node if jt.parent < 0 else base + jt.parent
        g.gltf["nodes"][parent].setdefault("children", []).append(base + i)
    # vertices stay in the attachment's model space, so its own inverse binds apply: at rest
    # v * INV_sub * W_sub * attach = v * attach
    ibm = np.array([gltf._mirror_matrix(m) for m in sub.inv_world_bind], np.float32)
    skins = g.gltf.setdefault("skins", [])
    skins.append({"name": name, "joints": list(range(base, base + len(sub.joints))),
                  "inverseBindMatrices": g.add_accessor(ibm, comps=16), "skeleton": base})
    return base, len(skins) - 1


TRACK_BIND_TOLERANCE = 0.01


def _track_matches(track, sub: M.Skeleton) -> bool:
    """Attachment tracks are matched by node count, but several rigs share a count (e.g. 19-joint capes
    and pauldrons with different joint orders). Accept a track only if its first-frame joint offsets
    agree with the rig's bind pose (clip space is Z-mirrored)."""
    bind = np.array([sub.local_bind[i][3][:3] for i in range(len(sub.joints))], np.float32)
    first = track.translations[0].astype(np.float32) * np.array([1, 1, -1], np.float32)
    idx = [i for i, jt in enumerate(sub.joints) if jt.parent >= 0]
    return bool(idx) and float(np.abs(bind[idx] - first[idx]).mean()) < TRACK_BIND_TOLERANCE


_roles_cache = {}


def clip_roles(an4_path: str) -> set:
    """Rig roles a clip drives ('Face', 'Cape', 'SkinnedHair' ...), from the .CLIP/.ANIM files that
    reference this .AN4. Those archives describe each animation as tracks with a RoleName."""
    folder = os.path.dirname(os.path.abspath(an4_path))
    if folder not in _roles_cache:
        from . import baked
        table = {}
        for f in sorted(os.listdir(folder)):
            if not f.upper().endswith((".CLIP", ".ANIM")):
                continue
            try:
                ar = baked.read_archive(open(os.path.join(folder, f), "rb").read())
                objs = baked.Reader(ar).read_olst()
            except Exception:
                continue
            found = {}

            def walk(o):
                if isinstance(o, dict):
                    if o.get("_class") == "AnimCurveAn4Ref":
                        res = (o.get("AN4 Resource") or {}).get("Resource_Path", "")
                        if res:
                            found.setdefault(os.path.basename(res).upper(), set()).add(o.get("RoleName") or "")
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)

            walk(objs)
            for k, v in found.items():
                table.setdefault(k, set()).update(v)
        _roles_cache[folder] = table
    return _roles_cache[folder].get(os.path.basename(an4_path).upper(), set())


ROLE_KEYWORDS = {"face": "Face", "cape": "Cape", "hair": "SkinnedHair", "skinnedhair": "SkinnedHair"}


def _rig_role(entity: str) -> str | None:
    low = entity.lower()
    for key, role in ROLE_KEYWORDS.items():
        if low.startswith(key) or key in low:
            return role
    return None


def load_an4_tracks(path: str) -> list:
    """All animation tracks of an AN4 (body, face rig, cape ...), first occurrence of each node count."""
    from . import anim
    data = open(path, "rb").read()
    tracks, seen = [], set()
    for base, endian in anim.find_headers(data):
        try:
            clip = anim.decode_clip(data, base, endian)
        except Exception:
            continue
        if clip.num_nodes not in seen:
            seen.add(clip.num_nodes)
            tracks.append(clip)
    return tracks


def character_to_glb(prefab_path: str, clips=()) -> bytes:
    """clips: [(name, [Clip, ...])] or [(name, [Clip, ...], {roles})] - all tracks of one animation
    (load_an4_tracks) and optionally the rig roles it drives (clip_roles)."""
    from .resource import read_resource
    parts = load_prefab(prefab_path)
    root = next((p for p in parts if p.is_root), None)
    if root is None:
        raise ValueError("prefab has no root render object")
    main_path = resolve_path(root.model)
    main = M.read_model(main_path)
    if not main.skeletons:
        raise ValueError("root model has no skeleton")
    skel = main.skeletons[0]
    g = gltf.GlbBuilder()
    arm, skin = gltf._add_skeleton(g, skel, "Armature")
    n = len(skel.joints)
    # (first joint node, joints, static joints, skeleton, role, joint counts of the rig's LODs)
    rigs = [(arm + 1, n, (), None, None, [len(sk.joints) for sk in main.skeletons])]
    inv = [np.linalg.inv(m).astype(np.float32) for m in skel.inv_world_bind]

    # main body
    root.path = main_path
    mats = MAT.read_materials(read_resource(main_path).body)
    for sp, meta in _lod0_specials(main, root.hidden_layers):
        rigid = meta.joint if meta.type == 0 and meta.joint >= 0 else None
        _add_part_meshes(g, main, mats, root, skin, n, [sp], rigid)

    # attachments
    joint_names = [j.name.lower() for j in skel.joints]
    for part in parts:
        if part.is_root or not part.model or not part.enabled:
            continue
        path = resolve_path(part.model)
        if not path:
            continue
        part.path = path
        if not part.attach_kind:
            # ADDITIONALMODEL_*: extra skinned geometry on the root skeleton (fur, armour panels ...)
            if not path.upper().endswith(".GHG"):
                continue
            try:
                mdl = M.read_model(path)
            except Exception:
                continue
            if not mdl.skeletons or [j.name.lower() for j in mdl.skeletons[0].joints] != joint_names:
                continue
            pm = MAT.read_materials(read_resource(path).body)
            for sp, meta in _lod0_specials(mdl, part.hidden_layers):
                rigid = meta.joint if meta.type == 0 and meta.joint >= 0 else None
                _add_part_meshes(g, mdl, pm, part, skin, n, [sp], rigid)
            continue
        joint, offset = None, np.eye(4, dtype=np.float32)
        if part.attach_kind == "joint":
            joint = _joint_index(skel, part.attach_name)
        else:
            poi = _poi(skel, part.attach_name)
            if poi:
                offset, joint = poi[0], poi[1]
        if joint is None or joint >= n:
            continue
        xform = offset @ inv[joint]
        push = None
        if part.entity.lower().startswith("face"):
            hb = _special_bounds(main, "Head_Mesh")
            if hb is not None:
                c = np.append((hb[0] + hb[1]) / 2, 1.0) @ skel.inv_world_bind[joint]   # head centre, joint-local
                t, st, ti = np.eye(4, dtype=np.float32), np.diag([DECAL_PUSH] * 3 + [1]).astype(np.float32), np.eye(4, dtype=np.float32)
                t[3, :3], ti[3, :3] = -c[:3], c[:3]
                push = t @ st @ ti
        try:
            mdl = M.read_model(path)
            pm = MAT.read_materials(read_resource(path).body)
        except Exception:
            continue
        if mdl.skeletons and RIGGED_ATTACHMENTS:
            sub = mdl.skeletons[0]
            base, sub_skin = _add_attachment_rig(g, sub, arm + 1 + joint, offset, part.entity, push)
            # rig roots carry the attach transform; their tracks are in another space, so leave them static
            rigs.append((base, len(sub.joints), {i for i, jt in enumerate(sub.joints) if jt.parent < 0},
                         sub, _rig_role(part.entity), [len(sk.joints) for sk in mdl.skeletons]))
            for sp, meta in _lod0_specials(mdl, part.hidden_layers):
                rigid = meta.joint if meta.type == 0 and meta.joint >= 0 else None
                _add_part_meshes(g, mdl, pm, part, sub_skin, len(sub.joints), [sp], rigid)
            continue
        if push is not None:
            xform = push @ xform
        if mdl.skeletons:
            specials = [sp for sp, _ in _lod0_specials(mdl, part.hidden_layers)]
        else:
            want = part.special.lower()
            specials = [sp for sp in mdl.specials if (not want or want.startswith("[") or sp.name.lower() == want)
                        and not sp.name.lower().startswith("loc_")]
        _add_part_meshes(g, mdl, pm, part, skin, n, specials, rigid_joint=joint, xform=xform)

    # animations: each clip drives the body and every attachment rig it has a track for. Which track
    # belongs to which rig comes from the clip metadata (.CLIP/.ANIM role names) when available,
    # since an .AN4 holds a track per skeleton LOD and several rigs can share a joint count.
    for entry in clips:
        name, tracks = entry[0], entry[1]
        roles = entry[2] if len(entry) > 2 else None
        tracks = tracks if isinstance(tracks, (list, tuple)) else [tracks]
        samplers, channels, used, reserved = [], [], set(), set()
        for base, count, static, sub, role, lods in rigs:
            if count in reserved:              # a lower LOD of a rig that already took its track
                continue

            def pick(validate):
                return next((i for i, t in enumerate(tracks) if i not in used and t.num_nodes == count
                             and (not validate or _track_matches(t, sub))), None)
            if sub is None:
                k = pick(False)
            elif roles is not None and role:
                k = pick(False) if role in roles else None
            else:
                k = pick(True)
            if k is None:
                continue
            used.add(k)
            reserved.update(c for c in lods if c != count)   # an .AN4 holds one track per skeleton LOD
            gltf.animation_channels(g, base, count, tracks[k], samplers=samplers, channels=channels, skip=static)
        if channels:
            g.gltf.setdefault("animations", []).append({"name": name, "samplers": samplers, "channels": channels})
    return g.to_glb()
