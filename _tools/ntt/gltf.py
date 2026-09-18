"""Minimal glTF 2.0 (.glb) writer for NTT models."""
import json
import struct

import numpy as np

from . import model as M

# NTT is left-handed Y-up (DirectX); glTF is right-handed Y-up. Mirror X.
MIRROR = np.diag([-1.0, 1.0, 1.0, 1.0]).astype(np.float32)

ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER = 34962, 34963
FLOAT, UNSIGNED_BYTE, UNSIGNED_SHORT, UNSIGNED_INT = 5126, 5121, 5123, 5125
TYPES = {1: "SCALAR", 2: "VEC2", 3: "VEC3", 4: "VEC4", 16: "MAT4"}


class GlbBuilder:
    def __init__(self):
        self.gltf = {"asset": {"version": "2.0", "generator": "tss-tools"},
                     "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [],
                     "accessors": [], "bufferViews": [], "buffers": [{"byteLength": 0}]}
        self.bin = bytearray()

    def add_accessor(self, arr: np.ndarray, target=None, normalized=False, minmax=False, comps=None):
        arr = np.ascontiguousarray(arr)
        while len(self.bin) % 4:
            self.bin.append(0)
        view = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": arr.nbytes}
        if target:
            view["target"] = target
        self.bin += arr.tobytes()
        self.gltf["bufferViews"].append(view)
        ctype = {np.float32: FLOAT, np.uint8: UNSIGNED_BYTE, np.uint16: UNSIGNED_SHORT,
                 np.uint32: UNSIGNED_INT}[arr.dtype.type]
        n = comps or (arr.shape[1] if arr.ndim > 1 else 1)
        acc = {"bufferView": len(self.gltf["bufferViews"]) - 1, "componentType": ctype,
               "count": arr.shape[0], "type": TYPES[n]}
        if normalized:
            acc["normalized"] = True
        if minmax:
            acc["min"] = arr.min(0).tolist()
            acc["max"] = arr.max(0).tolist()
        self.gltf["accessors"].append(acc)
        return len(self.gltf["accessors"]) - 1

    def add_node(self, node: dict, root=False) -> int:
        self.gltf["nodes"].append(node)
        i = len(self.gltf["nodes"]) - 1
        if root:
            self.gltf["scenes"][0]["nodes"].append(i)
        return i

    def to_glb(self) -> bytes:
        while len(self.bin) % 4:
            self.bin.append(0)
        self.gltf["buffers"][0]["byteLength"] = len(self.bin)
        js = json.dumps(self.gltf, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        total = 12 + 8 + len(js) + 8 + len(self.bin)
        return (struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
                + struct.pack("<I4s", len(self.bin), b"BIN\0") + bytes(self.bin))


def _mirror_matrix(m: np.ndarray) -> list:
    # Row-vector matrices stored row-major == glTF column-major order.
    return (MIRROR @ m @ MIRROR).astype(np.float32).flatten().tolist()


def _unorm(a):
    return a.astype(np.float32) / 255.0


def mesh_with_weights(g: "GlbBuilder", name: str, prims: list) -> dict:
    """glTF requires every primitive of a mesh to have the same morph target count, so parts that
    carry fewer blend shapes are padded with empty (zero-delta) targets."""
    mesh = {"name": name, "primitives": prims}
    most = max((len(p.get("targets", [])) for p in prims), default=0)
    if not most:
        return mesh
    for prim in prims:
        targets = prim.setdefault("targets", [])
        if len(targets) < most:
            count = g.gltf["accessors"][prim["attributes"]["POSITION"]]["count"]
            zeros = g.add_accessor(np.zeros((count, 3), np.float32), ARRAY_BUFFER, minmax=True)
            targets += [{"POSITION": zeros} for _ in range(most - len(targets))]
    mesh["weights"] = [0.0] * most
    return mesh


def is_proxy(part: M.MeshPart) -> bool:
    """Shadow-imposter / depth-only geometry: no UVs and no vertex colours."""
    sems = {a[0] for vb in part.streams for a in vb.attribs}
    return not sems & {M.UV0, M.UV1, M.COLOR0, M.COLOR1}


def part_primitive(g: GlbBuilder, part: M.MeshPart, num_joints: int | None, rigid_joint: int | None = None,
                   xform: np.ndarray | None = None):
    lo, hi = part.ib_base, part.ib_base + part.vb_used
    idx = part.ib.array()[part.ib_offset:part.ib_offset + part.ib_count].astype(np.uint32)
    if len(idx) < 3 or part.vb_used == 0:
        return None
    idx = idx[: len(idx) // 3 * 3].reshape(-1, 3)[:, ::-1]      # flip winding for the mirror
    attrs = {}

    pos, _ = part.attribute(M.POSITION)
    pos = pos[lo:hi, :3].astype(np.float32)
    if xform is not None:                       # row-vector transform (joint-local -> model)
        pos = pos @ xform[:3, :3] + xform[3, :3]
    pos = pos * np.array([-1, 1, 1], np.float32)
    attrs["POSITION"] = g.add_accessor(pos, ARRAY_BUFFER, minmax=True)

    got = part.attribute(M.NORMAL)
    if got is not None:
        a, typ = got
        n = (_unorm(a[lo:hi, :3]) * 2 - 1) if typ in (8, 9) else a[lo:hi, :3].astype(np.float32)
        if xform is not None:
            n = n @ xform[:3, :3]
        n *= np.array([-1, 1, 1], np.float32)
        length = np.linalg.norm(n, axis=1, keepdims=True)
        n = np.where(length > 1e-6, n / np.maximum(length, 1e-6), np.array([0, 1, 0], np.float32))
        attrs["NORMAL"] = g.add_accessor(n.astype(np.float32), ARRAY_BUFFER)

    got = part.attribute(M.TANGENT)
    if got is not None:
        a, typ = got
        t = (_unorm(a[lo:hi, :3]) * 2 - 1) if typ in (8, 9) else a[lo:hi, :3].astype(np.float32)
        if xform is not None:
            t = t @ xform[:3, :3]
        t *= np.array([-1, 1, 1], np.float32)
        length = np.linalg.norm(t, axis=1, keepdims=True)
        t = np.where(length > 1e-6, t / np.maximum(length, 1e-6), np.array([1, 0, 0], np.float32))
        tan = np.ones((len(t), 4), np.float32)          # w: handedness, restored as 1 on import
        tan[:, :3] = t
        attrs["TANGENT"] = g.add_accessor(tan, ARRAY_BUFFER)

    for sem, name in ((M.UV0, "TEXCOORD_0"), (M.UV1, "TEXCOORD_1")):
        got = part.attribute(sem)
        if got is not None:
            a, _ = got
            attrs[name] = g.add_accessor(a[lo:hi, :2].astype(np.float32), ARRAY_BUFFER)
            if sem == M.UV0 and a.shape[1] >= 4 and "TEXCOORD_1" not in attrs:
                attrs["TEXCOORD_1"] = g.add_accessor(np.ascontiguousarray(a[lo:hi, 2:4], np.float32), ARRAY_BUFFER)

    got = part.attribute(M.COLOR0)
    if got is not None:
        a, _ = got
        attrs["COLOR_0"] = g.add_accessor(np.ascontiguousarray(a[lo:hi, :4]), ARRAY_BUFFER, normalized=True)

    joints, weights = part.attribute(M.JOINTS), part.attribute(M.WEIGHTS)
    if num_joints and rigid_joint is not None:
        n = hi - lo
        j = np.zeros((n, 4), np.uint16)
        j[:, 0] = rigid_joint
        w = np.zeros((n, 4), np.float32)
        w[:, 0] = 1
        attrs["JOINTS_0"] = g.add_accessor(j, ARRAY_BUFFER)
        attrs["WEIGHTS_0"] = g.add_accessor(w, ARRAY_BUFFER)
    elif num_joints and joints is not None and weights is not None:
        j = joints[0][lo:hi].astype(np.uint16)
        if len(part.skin_map):
            remap = np.frombuffer(part.skin_map, np.uint8).astype(np.uint16)
            j = remap[np.minimum(j, len(remap) - 1)]
        w = _unorm(weights[0][lo:hi])
        s = w.sum(1, keepdims=True)
        w = np.where(s > 0, w / np.maximum(s, 1e-6), np.array([1, 0, 0, 0], np.float32))
        j = np.where(w > 0, j, 0).astype(np.uint16)
        if int(j.max()) < num_joints:
            attrs["JOINTS_0"] = g.add_accessor(j, ARRAY_BUFFER)
            attrs["WEIGHTS_0"] = g.add_accessor(w.astype(np.float32), ARRAY_BUFFER)

    if part.blend_shapes:
        targets = []
        for indices, deltas in part.blend_shapes:
            d = np.zeros((hi - lo, 3), np.float32)
            sel = indices.astype(np.int64) - lo
            keep = (sel >= 0) & (sel < hi - lo)
            if not keep.any():
                continue
            dv = deltas[keep].astype(np.float32)
            if xform is not None:
                dv = dv @ xform[:3, :3]
            d[sel[keep]] = dv * np.array([-1, 1, 1], np.float32)
            targets.append({"POSITION": g.add_accessor(d, ARRAY_BUFFER, minmax=True)})
        if targets:
            return {"attributes": attrs, "targets": targets,
                    "indices": g.add_accessor(idx.astype(np.uint32).flatten(), ELEMENT_ARRAY_BUFFER, comps=1),
                    "mode": 4}

    return {"attributes": attrs,
            "indices": g.add_accessor(idx.astype(np.uint32).flatten(), ELEMENT_ARRAY_BUFFER, comps=1),
            "mode": 4}


TEXTURE_MAX_SIZE = 2048


def _image(g: GlbBuilder, tid: int) -> int | None:
    """Embed texture table entry `tid` (see model_to_glb textures=) and return a glTF texture index."""
    cache = g.__dict__.setdefault("_img_cache", {})
    if tid in cache:
        return cache[tid]
    cache[tid] = None
    table = g.__dict__.get("texture_table") or []
    if tid is None or not (0 <= tid < len(table)) or table[tid][1] is None:
        return None
    name, dds_bytes = table[tid]
    import io
    from PIL import Image
    from . import dds
    try:
        info = dds.parse_dds_header(dds_bytes)
        if info.fmt is None or info.width == 0:
            return None
        rgba = dds.decode_rgba(info.fmt, dds_bytes[info.header_size:], info.width, info.height)
    except Exception:
        return None
    img = Image.fromarray(rgba, "RGBA")
    limit = g.__dict__.get("texture_max", TEXTURE_MAX_SIZE)
    if limit and max(img.size) > limit:
        img.thumbnail((limit, limit), Image.LANCZOS)
    buf = io.BytesIO()
    if rgba[..., 3].min() == 255:
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
    g.gltf.setdefault("images", []).append({"name": name.rsplit("/", 1)[-1], "mimeType": mime,
                                            "bufferView": len(g.gltf["bufferViews"]) - 1})
    g.gltf.setdefault("samplers", [{"magFilter": 9729, "minFilter": 9987}])
    g.gltf.setdefault("textures", []).append({"source": len(g.gltf["images"]) - 1, "sampler": 0})
    cache[tid] = len(g.gltf["textures"]) - 1
    return cache[tid]


def _material(g: GlbBuilder, index: int, mdl: M.Model | None = None) -> int:
    mats = g.gltf.setdefault("materials", [])
    lookup = g.__dict__.setdefault("_mat_lookup", {})
    if index not in lookup:
        mat = {"name": f"material_{index:03d}",
               "pbrMetallicRoughness": {"metallicFactor": 0.0, "roughnessFactor": 0.5}}
        materials = g.__dict__.get("materials") or []
        if 0 <= index < len(materials):
            m = materials[index]
            mat["name"] = m.name or mat["name"]
            if (ti := _image(g, m.diffuse[0])) is not None:
                mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": ti}
            if (ti := _image(g, m.normal[0])) is not None:
                mat["normalTexture"] = {"index": ti}
            if m.blend_mode:
                mat["alphaMode"] = "BLEND"
            mat["extras"] = {k: v for k, v in m.fields.items()
                             if k in ("m_ShaderType", "m_BlendMode", "m_AlphaTest", "m_IsTPaged", "m_IsDecal",
                                      "kTPageID", "m_NumUVSets", "cull")}
        mats.append(mat)
        lookup[index] = len(mats) - 1
    return lookup[index]


def _is_shadow_material(g, index):
    materials = g.__dict__.get("materials") or []
    return 0 <= index < len(materials) and materials[index].is_shadow_only


def _add_object_mesh(g, mdl, special, num_joints=None, rigid_joint=None, xform=None):
    items = mdl.clip_objects[special.clip_object] if 0 <= special.clip_object < len(mdl.clip_objects) else []
    prims = []
    for item in items:
        if item.mesh >= len(mdl.parts):
            continue
        if not g.__dict__.get("keep_proxies"):
            if _is_shadow_material(g, item.material):
                continue
            if not g.__dict__.get("materials") and is_proxy(mdl.parts[item.mesh]):
                continue
        prim = part_primitive(g, mdl.parts[item.mesh], num_joints, rigid_joint, xform)
        if prim is not None:
            prim["material"] = _material(g, item.material, mdl)
            prims.append(prim)
    if not prims:
        return None
    g.gltf["meshes"].append(mesh_with_weights(g, special.name, prims))
    return len(g.gltf["meshes"]) - 1


def _add_skeleton(g, skel, name):
    base = len(g.gltf["nodes"])
    root = g.add_node({"name": name, "children": []}, root=True)
    base = root + 1
    for i, jt in enumerate(skel.joints):
        m = skel.local_bind[i] if i < len(skel.local_bind) else np.eye(4, dtype=np.float32)
        g.add_node({"name": jt.name, "matrix": _mirror_matrix(m)})
        if jt.parent < 0:
            g.gltf["nodes"][root]["children"].append(base + i)
    for i, jt in enumerate(skel.joints):
        if jt.parent >= 0:
            g.gltf["nodes"][base + jt.parent].setdefault("children", []).append(base + i)
    ibm = np.array([_mirror_matrix(m) for m in skel.inv_world_bind], np.float32)
    skins = g.gltf.setdefault("skins", [])
    skins.append({"name": name, "joints": list(range(base, base + len(skel.joints))),
                  "inverseBindMatrices": g.add_accessor(ibm, comps=16), "skeleton": base})
    return root, len(skins) - 1


BREAKUP_WORDS = ("breakup", "blowup", "killpart")


def animation_channels(g: GlbBuilder, joint_base: int, num_joints: int, clip, fps: float = 30.0,
                       samplers=None, channels=None, skip=()):
    """Append samplers/channels driving joint nodes joint_base..+num_joints from a clip (ntt.anim.Clip).

    Clip space is the engine space with Z mirrored and its rotations are row-vector (transposed)
    matrices, while glTF output mirrors X. Calibrated against joints a clip leaves static (they must
    reproduce the bind pose): translations map (x, y, z) -> (-x, y, -z) and quaternions
    (x, y, z, w) -> (-x, -y, z, w).
    """
    samplers = [] if samplers is None else samplers
    channels = [] if channels is None else channels
    n = min(num_joints, clip.num_nodes)
    times = (np.arange(clip.num_frames, dtype=np.float32) / fps).reshape(-1, 1)
    t_acc = g.add_accessor(times, minmax=True)
    flip = np.array([-1, 1, -1], np.float32)
    qflip = np.array([-1, -1, 1, 1], np.float32)
    for j in range(n):
        if j in skip:
            continue
        pos = np.ascontiguousarray(clip.translations[:, j, :] * flip)
        rot = clip.rotations[:, j, :] * qflip
        for k in range(1, len(rot)):                  # keep quaternion hemisphere continuous
            if float(np.dot(rot[k], rot[k - 1])) < 0:
                rot[k] = -rot[k]
        samplers.append({"input": t_acc, "output": g.add_accessor(pos), "interpolation": "LINEAR"})
        channels.append({"sampler": len(samplers) - 1, "target": {"node": joint_base + j, "path": "translation"}})
        samplers.append({"input": t_acc, "output": g.add_accessor(np.ascontiguousarray(rot, np.float32)),
                         "interpolation": "LINEAR"})
        channels.append({"sampler": len(samplers) - 1, "target": {"node": joint_base + j, "path": "rotation"}})
    return samplers, channels


def add_animation(g: GlbBuilder, joint_base: int, num_joints: int, clip, name: str, fps: float = 30.0):
    samplers, channels = animation_channels(g, joint_base, num_joints, clip, fps)
    g.gltf.setdefault("animations", []).append({"name": name, "samplers": samplers, "channels": channels})


def model_to_glb(mdl: M.Model, lods=(0,), breakups=False, textures: list | None = None,
                 keep_proxies=False, clips=(), materials: list | None = None, texture_max=TEXTURE_MAX_SIZE) -> bytes:
    """Characters: one armature per selected skeleton LOD with its layers.
    Scenery/props: one node per named object.
    textures: texture table [(name, dds bytes or None)] indexed by material texture ids.
    materials: ntt.material.Material list (material index order)."""
    g = GlbBuilder()
    g.texture_table = textures or []
    g.materials = materials or []
    g.texture_max = texture_max
    g.keep_proxies = keep_proxies
    if mdl.skeletons:
        for lod in lods:
            if lod >= len(mdl.skeletons):
                continue
            skel = mdl.skeletons[lod]
            root, skin = _add_skeleton(g, skel, f"LOD{lod}" if len(lods) > 1 else "Armature")
            if lod == lods[0]:
                for clip_name, clip in clips:
                    add_animation(g, root + 1, len(skel.joints), clip, clip_name)
            layer_of = {}
            for layer in skel.layers:
                for k in range(layer.meta_index, layer.meta_index + layer.num_rigids + layer.num_skins):
                    layer_of[k] = layer.name
            for k, meta in enumerate(skel.layer_meta):
                if meta.special >= len(mdl.specials):
                    continue
                special = mdl.specials[meta.special]
                layer_name = layer_of.get(k, '')
                is_breakup = any(w in (special.name + layer_name).lower() for w in BREAKUP_WORDS)
                if is_breakup and not breakups:
                    continue
                if special.name.lower().startswith("zhead") and not keep_proxies:
                    continue                               # depth pre-pass copy of the head
                rigid = meta.joint if meta.type == 0 and meta.joint >= 0 else None
                # Rigid parts are authored in model space, except destruction debris which is joint-local.
                xform = None
                if rigid is not None and is_breakup:
                    xform = np.linalg.inv(skel.inv_world_bind[rigid]).astype(np.float32)
                mesh = _add_object_mesh(g, mdl, special, len(skel.joints), rigid, xform)
                if mesh is None:
                    continue
                label = f"{layer_name}:{special.name}".lstrip(":")
                g.add_node({"name": label, "mesh": mesh, "skin": skin}, root=True)
    else:
        for special in mdl.specials:
            mesh = _add_object_mesh(g, mdl, special)
            if mesh is None:
                continue
            node = {"name": special.name, "mesh": mesh}
            if np.any(special.matrix) and not np.allclose(special.matrix, np.eye(4)):
                node["matrix"] = _mirror_matrix(special.matrix)
            g.add_node(node, root=True)
    return g.to_glb()
