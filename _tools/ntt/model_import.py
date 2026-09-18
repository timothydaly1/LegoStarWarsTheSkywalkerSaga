"""Replace the geometry of a .GHG/.GSC mesh part with a mesh from a glTF/GLB file (modding).

The model body is patched in place: each vertex buffer's data and count, the index buffer, the
part's vbUsedCount/ibCount/ibOffset/ibBase and its bounds. Blocks after MESH simply shift, which is
safe because nothing in the body stores absolute byte offsets (checked across the NU20 blocks), and
the body size field at body[4:8] is updated.

New vertices are encoded in the part's own vertex format (same semantics, types and stride), so a
replacement mesh keeps working with the original material and skeleton. glTF JOINTS_0 indices are
taken as-is, which matches models exported by this toolkit (skin joint order = skeleton order).
"""
import json
import struct

import numpy as np

from . import model as M
from .resource import parse_resource

# vertex attribute semantic -> glTF attribute name
SEMANTIC_ATTR = {M.POSITION: "POSITION", M.NORMAL: "NORMAL", M.TANGENT: "TANGENT",
                 M.COLOR0: "COLOR_0", M.COLOR1: "COLOR_1", M.UV0: "TEXCOORD_0", M.UV1: "TEXCOORD_1",
                 M.JOINTS: "JOINTS_0", M.WEIGHTS: "WEIGHTS_0"}
DEFAULTS = {M.NORMAL: (0.0, 1.0, 0.0, 1.0), M.TANGENT: (1.0, 0.0, 0.0, 1.0),
            M.COLOR0: (1.0, 1.0, 1.0, 1.0), M.COLOR1: (1.0, 1.0, 1.0, 1.0),
            M.WEIGHTS: (1.0, 0.0, 0.0, 0.0)}
MIRROR = np.array([-1, 1, 1], np.float32)      # exporters mirror X; importing mirrors back


# --- glTF reading ------------------------------------------------------------

def read_glb(path: str):
    with open(path, "rb") as f:
        data = f.read()
    if data[:4] == b"glTF":
        n = struct.unpack_from("<I", data, 12)[0]
        gltf = json.loads(data[20:20 + n])
        bin_start = 20 + n + 8
        buf = data[bin_start:]
    else:
        gltf = json.loads(data)
        buf = b""
    return gltf, buf


_COMP = {5120: ("<i1", 1), 5121: ("u1", 1), 5122: ("<i2", 2), 5123: ("<u2", 2),
         5125: ("<u4", 4), 5126: ("<f4", 4)}
_NCOMP = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def accessor(gltf, buf, index) -> np.ndarray:
    a = gltf["accessors"][index]
    v = gltf["bufferViews"][a["bufferView"]]
    dtype, size = _COMP[a["componentType"]]
    n = _NCOMP[a["type"]]
    stride = v.get("byteStride") or size * n
    start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    raw = np.frombuffer(buf, np.uint8, stride * (a["count"] - 1) + size * n, start)
    out = np.empty((a["count"], n), dtype)
    for i in range(a["count"]):
        out[i] = np.frombuffer(raw[i * stride:i * stride + size * n].tobytes(), dtype)
    if a.get("normalized") and dtype in ("u1", "<u2"):
        return out.astype(np.float32) / (255.0 if dtype == "u1" else 65535.0)
    return out


def load_mesh(path: str, name: str | None = None) -> dict:
    """-> {attribute: array, 'INDICES': array} for one glTF mesh (all primitives merged)."""
    gltf, buf = read_glb(path)
    meshes = gltf.get("meshes", [])
    mesh = None
    if name:
        mesh = next((m for m in meshes if m.get("name") == name), None)
        if mesh is None:
            mesh = next((m for m in meshes if name.lower() in (m.get("name") or "").lower()), None)
        if mesh is None:
            raise ValueError(f"{path}: no mesh matching {name!r} (have {[m.get('name') for m in meshes]})")
    else:
        if len(meshes) != 1:
            raise ValueError(f"{path}: {len(meshes)} meshes, name one of {[m.get('name') for m in meshes]}")
        mesh = meshes[0]
    attrs, indices, base = {}, [], 0
    for prim in mesh["primitives"]:
        if prim.get("mode", 4) != 4:
            raise ValueError("only triangle primitives can be imported")
        count = gltf["accessors"][prim["attributes"]["POSITION"]]["count"]
        for key, acc in prim["attributes"].items():
            attrs.setdefault(key, []).append(accessor(gltf, buf, acc))
        if "indices" in prim:
            indices.append(accessor(gltf, buf, prim["indices"]).reshape(-1).astype(np.uint32) + base)
        else:
            indices.append(np.arange(base, base + count, dtype=np.uint32))
        base += count
    out = {}
    for key, chunks in attrs.items():
        want = max(c.shape[1] for c in chunks)
        fixed = []
        for c in chunks:
            if c.shape[1] < want:
                pad = np.zeros((len(c), want), c.dtype)
                pad[:, :c.shape[1]] = c
                c = pad
            fixed.append(c)
        out[key] = np.concatenate(fixed)
    out["INDICES"] = np.concatenate(indices) if indices else np.zeros(0, np.uint32)
    return out


# --- vertex encoding ---------------------------------------------------------

def _column(mesh: dict, semantic: int, count: int, comps: int) -> np.ndarray:
    key = SEMANTIC_ATTR.get(semantic)
    arr = mesh.get(key) if key else None
    out = np.zeros((count, comps), np.float32)
    if semantic in DEFAULTS:
        out[:] = np.array(DEFAULTS[semantic], np.float32)[:comps]
    if arr is None:
        return out
    a = np.asarray(arr, np.float32)
    if semantic in (M.POSITION, M.NORMAL, M.TANGENT):
        a = a.copy()
        a[:, :3] *= MIRROR
    n = min(comps, a.shape[1])
    out[:, :n] = a[:, :n]
    if semantic == M.UV0 and comps == 4 and "TEXCOORD_1" in mesh:      # second UV set lives in zw
        uv1 = np.asarray(mesh["TEXCOORD_1"], np.float32)
        out[:, 2:4] = uv1[:, :2]
    if semantic in (M.TANGENT, M.NORMAL) and comps == 4 and a.shape[1] < 4:
        out[:, 3] = 1.0
    if semantic == M.POSITION and comps == 4:
        out[:, 3] = 1.0
    return out


def encode_vertices(vb: M.VertexBuffer, mesh: dict, skin_map: bytes = b"") -> tuple:
    """-> (bytes, vertex count) in the buffer's own format.

    Normals/tangents are stored unsigned-normalized ((v + 1) / 2), weights as v * 255 and joint
    indices through the part's skin map palette (glTF uses skeleton joint indices)."""
    count = len(mesh["POSITION"])
    data = np.zeros((count, vb.stride), np.uint8)
    inverse = {}
    if skin_map:
        for local, joint in enumerate(np.frombuffer(skin_map, np.uint8).tolist()):
            inverse.setdefault(joint, local)
    for sem, typ, off in vb.attribs:
        dtype, comps, size = M.VTYPES[typ]
        col = _column(mesh, sem, count, comps)
        if sem == M.JOINTS:
            j = np.asarray(mesh.get("JOINTS_0", np.zeros((count, comps))), np.int64)[:, :comps]
            if inverse:
                unknown = sorted(set(np.unique(j).tolist()) - set(inverse))
                if unknown:
                    raise ValueError(f"vertices use joints {unknown[:8]} that are not in the part's skin map")
                j = np.vectorize(inverse.get)(j)
            enc = np.clip(j, 0, 255).astype(np.uint8).tobytes()
        elif sem in (M.NORMAL, M.TANGENT) and typ in (8, 9):
            enc = np.clip((col * 0.5 + 0.5) * 255.0 + 0.5, 0, 255).astype(np.uint8).tobytes()
        elif typ == 7:
            enc = np.clip(col, 0, 255).astype(np.uint8).tobytes()
        elif typ in (8, 9):
            enc = np.clip(col * 255.0 + 0.5, 0, 255).astype(np.uint8).tobytes()
        elif dtype == "<f2":
            enc = col.astype(np.float16).tobytes()
        else:
            enc = col.astype(np.float32).tobytes()
        data[:, off:off + size] = np.frombuffer(enc, np.uint8).reshape(count, size)
    return data.tobytes(), count


# --- patching ----------------------------------------------------------------

def _apply(body: bytes, patches: list) -> bytes:
    """patches: [(offset, length, new bytes)] -> new body with the size field updated."""
    out = bytearray()
    prev = 0
    for off, length, new in sorted(patches):
        if off < prev:
            raise ValueError("overlapping patches")
        out += body[prev:off] + new
        prev = off + length
    out += body[prev:]
    struct.pack_into(">I", out, 4, len(out) - 8)      # body size field
    return bytes(out)


def replace_part(model_path: str, part_index: int, mesh: dict, out_path: str) -> dict:
    """Replace one mesh part's geometry with `mesh` (from load_mesh) and write a new model file."""
    with open(model_path, "rb") as f:
        raw = f.read()
    res = parse_resource(raw, model_path)
    body = res.body
    mdl = M.read_model(model_path)
    if not 0 <= part_index < len(mdl.parts):
        raise ValueError(f"part {part_index} out of range (model has {len(mdl.parts)})")
    part = mdl.parts[part_index]
    if len(part.streams) != 1:
        raise ValueError(f"part {part_index} has {len(part.streams)} vertex streams; only single-stream parts "
                         "can be replaced so far")
    vb = part.streams[0]
    users = [p for p in mdl.parts if p.index != part_index
             and (vb.id in {s.id for s in p.streams} or p.ib.id == part.ib.id)]
    vdata, count = encode_vertices(vb, mesh, part.skin_map)
    idx = np.asarray(mesh["INDICES"], np.uint32).reshape(-1, 3)[:, ::-1].reshape(-1)   # undo the export mirror
    if count and idx.max(initial=0) >= count:
        raise ValueError("index out of range")
    isize = part.ib.size
    idata = idx.astype("<u2" if isize == 2 else "<u4").tobytes()

    pos = np.asarray(mesh["POSITION"], np.float32).copy()
    pos[:, :3] *= MIRROR
    lo, hi = pos[:, :3].min(0), pos[:, :3].max(0)
    centre = np.append((lo + hi) / 2, 1.0).astype(">f4")
    extents = np.append((hi - lo) / 2, 0.0).astype(">f4")

    if users:
        # buffers shared with other parts (characters keep one buffer per LOD group, and parts may even
        # overlap): append the new geometry and point this part at it, leaving every other part untouched
        base, offset = vb.count, part.ib.count
        if base + count > 0xFFFFFFFF:
            raise ValueError("vertex buffer too large")
        patches = [
            (vb.count_offset, 4, struct.pack(">I", base + count)),
            (vb.data_offset + len(vb.data), 0, vdata),
            (part.ib.count_offset, 4, struct.pack(">I", offset + len(idx))),
            (part.ib.data_offset + len(part.ib.data), 0, idata),
            (part.ib_fields_offset, 12, struct.pack(">3I", offset, len(idx), base)),
            (part.vb_used_offset, 4, struct.pack(">I", count)),
            (part.bounds_offset, 32, centre.tobytes() + extents.tobytes()),
        ]
        shared_note = f"appended (buffer shared with {len(users)} other parts)"
    else:
        if count > 0xFFFF and isize == 2:
            raise ValueError("too many vertices for a 16-bit index buffer")
        patches = [
            (vb.count_offset, 4, struct.pack(">I", count)),
            (vb.data_offset, len(vb.data), vdata),
            (part.ib.count_offset, 4, struct.pack(">I", len(idx))),
            (part.ib.data_offset, len(part.ib.data), idata),
            (part.ib_fields_offset, 12, struct.pack(">3I", 0, len(idx), 0)),
            (part.vb_used_offset, 4, struct.pack(">I", count)),
            (part.bounds_offset, 32, centre.tobytes() + extents.tobytes()),
        ]
        shared_note = "replaced in place"
    new_body = _apply(body, patches)
    with open(out_path, "wb") as f:
        f.write(raw[:len(raw) - len(body)] + new_body)
    return {"part": part_index, "vertices": count, "triangles": len(idx) // 3, "how": shared_note,
            "was": (part.vb_used, part.ib_count // 3), "size_delta": len(new_body) - len(body)}
