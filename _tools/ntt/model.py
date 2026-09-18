"""Models: .GHG (characters/skinned) and .GSC (scenery/props) NU20 containers.

Body layout: u32 hash, u32 size, u32 1, 'NU20' (stored '02UN'), then a stream of
tagged blocks. Headers/tables are big-endian; GPU vertex/index data is
little-endian.  Tags are stored byte-reversed; names below are logical.

    INFO  NTBL(string table)  ...  MESH  UMTL(materials)  ...  CPUS  DISP
    TANB  BSCB  OCCB  IVL5  HGOL*(skeletons)  META

MESH (v201):
    u32 numParts
    part:
        u32 1, 'RNMS', u32 ver, u32 numStreams
        numStreams x (VB pointer, u32 byteOffset)
        u32 fastBlendVB (0)
        IB pointer
        u32 ibOffset, ibCount, ibBase ; u16 primType ; u32 vbUsedCount, instBits
        u32 skinMapSize + u8[skinMapSize] ; u32 dynamicBuffers (0) ; u32 optFlags
        f32[4] centre, f32[4] extents, f32 densityDiscDiameter, u32 depthBits

    pointer: u32 0 = null, 1 = object follows inline, 0xC0000000|id + u32 = back-reference
    VB object:  u32 flags, u32 count, 'VTXD', u32 ver, u32 numAttribs,
                numAttribs x (u8 semantic, u8 type, u8 offset), 6 bytes, vertex data
    IB object:  u32 flags, u32 count, u32 bytesPerIndex, index data

Serialized-object ids (for back-references) count every part, every RNMS
list and every inline VB/IB in file order, starting at 2.

HGOL (skeleton, v17):
    u32 0, u32 numJoints, joint x (str16 name, f32[16] orient, f32[3] offset, u8 parent, u8 flags)
    u32 0, u32 n, f32[16] x n   local bind transforms (row-vector, translation in row 3)
    u32 0, u32 n, f32[16] x n   inverse world bind transforms
"""
import struct
from dataclasses import dataclass, field

import numpy as np

from .resource import parse_resource

# vertex attribute semantics
POSITION, NORMAL, COLOR0, TANGENT, COLOR1, UV0, UNK6, UV1, UNK8, JOINTS, WEIGHTS = range(11)
SEMANTIC_NAMES = {0: "position", 1: "normal", 2: "color0", 3: "tangent", 4: "color1", 5: "uv0",
                  6: "unk6", 7: "uv1", 8: "unk8", 9: "joints", 10: "weights", 11: "unk11",
                  12: "lightdir", 13: "lightcol"}
# vertex attribute types -> (numpy dtype, components, byte size)
VTYPES = {
    2: ("<f4", 2, 8), 3: ("<f4", 3, 12), 4: ("<f4", 4, 16),
    5: ("<f2", 2, 4), 6: ("<f2", 4, 8),
    7: ("u1", 4, 4),   # raw bytes (blend indices)
    8: ("u1", 4, 4),   # unsigned-normalized bytes (normals, tangents, weights)
    9: ("u1", 4, 4),   # colour
}


class FormatError(ValueError):
    pass


class Reader:
    def __init__(self, data: bytes, offset: int = 0):
        self.b = data
        self.o = offset

    def u8(self):
        v = self.b[self.o]
        self.o += 1
        return v

    def u16(self):
        v, = struct.unpack_from(">H", self.b, self.o)
        self.o += 2
        return v

    def u32(self):
        v, = struct.unpack_from(">I", self.b, self.o)
        self.o += 4
        return v

    def f32(self, n=1):
        v = struct.unpack_from(f">{n}f", self.b, self.o)
        self.o += 4 * n
        return v if n > 1 else v[0]

    def raw(self, n):
        v = self.b[self.o:self.o + n]
        self.o += n
        return v

    def str16(self):
        n = self.u16()
        return self.raw(n).split(b"\0", 1)[0].decode("latin-1")

    def tag(self, name: str):
        want = name.encode()[::-1]
        got = self.b[self.o:self.o + 4]
        if got != want:
            raise FormatError(f"expected {name} at {self.o:#x}, got {got!r}")
        self.o += 4


@dataclass
class VertexBuffer:
    id: int
    flags: int
    count: int
    stride: int
    attribs: list          # (semantic, type, offset)
    data: bytes
    count_offset: int = 0  # byte offset of the u32 count in the body
    data_offset: int = 0   # byte offset of the vertex data in the body

    def attribute(self, semantic: int) -> np.ndarray | None:
        for sem, typ, off in self.attribs:
            if sem == semantic:
                dtype, comps, size = VTYPES[typ]
                raw = np.frombuffer(self.data, np.uint8).reshape(self.count, self.stride)
                arr = np.frombuffer(raw[:, off:off + size].tobytes(), dtype).reshape(self.count, comps)
                return arr, typ
        return None


@dataclass
class IndexBuffer:
    id: int
    flags: int
    count: int
    size: int
    data: bytes
    count_offset: int = 0
    data_offset: int = 0

    def array(self) -> np.ndarray:
        return np.frombuffer(self.data, "<u2" if self.size == 2 else "<u4")


@dataclass
class MeshPart:
    index: int
    streams: list          # VertexBuffer per stream
    ib: IndexBuffer
    ib_offset: int
    ib_count: int
    ib_base: int
    prim_type: int
    vb_used: int
    skin_map: bytes
    centre: tuple
    extents: tuple
    start: int = 0         # serialized byte range (from the RNMS tag)
    end: int = 0
    ib_fields_offset: int = 0   # u32 ibOffset, ibCount, ibBase
    vb_used_offset: int = 0     # u32 vbUsedCount
    bounds_offset: int = 0      # f32[4] centre, f32[4] extents
    blend_shapes: list = field(default_factory=list)   # [(indices, deltas)] sparse morph targets

    def attribute(self, semantic):
        for vb in self.streams:
            got = vb.attribute(semantic)
            if got is not None:
                return got
        return None


@dataclass
class Joint:
    name: str
    orient: np.ndarray
    offset: tuple
    parent: int            # -1 for root
    flags: int


@dataclass
class LayerMeta:
    type: int              # 1 = skinned, 0 = rigid (attached to joint)
    joint: int
    special: int
    layer: int


@dataclass
class Layer:
    name: str
    meta_index: int
    num_rigids: int
    num_skins: int


@dataclass
class Skeleton:
    joints: list
    local_bind: list       # 4x4 row-vector matrices
    inv_world_bind: list
    pois: list = field(default_factory=list)          # (name, matrix, parent joint)
    layer_meta: list = field(default_factory=list)
    layers: list = field(default_factory=list)


@dataclass
class ClipItem:
    material: int
    transform: int
    lightmap: int
    mesh: int
    lightmap_type: int
    transform_type: int
    geom_type: int


@dataclass
class Special:
    """A named drawable object (NuSpecialObject)."""
    name: str
    matrix: np.ndarray
    bounds_min: tuple
    bounds_max: tuple
    sphere: tuple
    clip_object: int
    flags: int
    instance: int
    anim: int


@dataclass
class Model:
    path: str
    source_path: str
    strings: bytes
    parts: list = field(default_factory=list)
    skeletons: list = field(default_factory=list)
    clip_objects: list = field(default_factory=list)   # list[list[ClipItem]]
    specials: list = field(default_factory=list)
    num_materials: int = 0
    materials: list | None = None                      # [(name, [texture names])] when reliable

    def string(self, offset: int) -> str:
        end = self.strings.find(b"\0", offset)
        return self.strings[offset:end].decode("latin-1")


DYNAMIC_BUFFERS_SERIALIZE = 0x14341a2c0
REGISTER_OBJECT = 0x1400d9f10
_emu = None


def _skip_dynamic_buffers(data: bytes, pos: int, version: int):
    """Run the game's NuDynamicBuffers serializer over the blend-shape block.

    -> (end offset, objects registered, [BlendShape]). The emulator tells us where each
    'm_buffer' lives; the buffer itself is a sparse vertex-delta list (see decode_blend_shape)."""
    global _emu
    import os, sys
    tools = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import emu as E
    from unicorn import UC_HOOK_CODE
    if _emu is None or _emu.heap_ptr - E.HEAP > E.HEAP_SIZE * 0.7:
        _emu = E.Emu()
    stream = E.Stream(_emu, data, pos)
    ser = E.make_serializer(_emu, stream, version)
    import fieldlog as FL
    count = [0]
    hook = _emu.mu.hook_add(UC_HOOK_CODE, lambda mu, a, sz, u: count.__setitem__(0, count[0] + 1),
                            begin=REGISTER_OBJECT, end=REGISTER_OBJECT)
    log = FL.FieldLog(_emu, stream)
    try:
        _emu.call(DYNAMIC_BUFFERS_SERIALIZE, [_emu.alloc(0x400), ser])
    finally:
        log.flush()
        log.detach()
        _emu.mu.hook_del(hook)
    spans, prev = [], None
    for p2, name, kind, val in log.values + [(stream.pos, "", "", None)]:
        if prev is not None and p2 > prev:
            spans.append((prev, p2))
            prev = None
        if name == "m_buffer":
            prev = p2
    shapes = []
    for a, b2 in spans:
        try:
            shapes.append(decode_blend_shape(data[a:b2]))
        except (struct.error, ValueError):
            pass
    return stream.pos, count[0], [s2 for s2 in shapes if len(s2[0])]


@dataclass
class BlendShape:
    indices: np.ndarray        # vertex indices this shape moves
    deltas: np.ndarray         # (n, 3) position deltas


def decode_blend_shape(buf: bytes):
    """Sparse vertex deltas: u32 first index, then per vertex 3 big-endian floats and the
    u32 step to the next index; trailing zero padding."""
    idx, out_i, out_d = struct.unpack_from(">I", buf, 0)[0], [], []
    o = 4
    while o + 12 <= len(buf):
        d = struct.unpack_from(">3f", buf, o)
        o += 12
        if any(abs(v) > 100 for v in d):
            break
        out_i.append(idx)
        out_d.append(d)
        if o + 4 > len(buf):
            break
        step = struct.unpack_from(">I", buf, o)[0]
        o += 4
        if step == 0:
            break
        idx += step
    return np.array(out_i, np.uint32), np.array(out_d, np.float32)


def _read_parts(r: Reader, tagged: bool = True) -> list:
    objects = {}
    next_id = [2]

    def new_id():
        i = next_id[0]
        next_id[0] += 1
        return i

    def pointer(kind, read_inline):
        v = r.u32()
        if v == 0:
            return None
        if v & 0xC0000000 == 0xC0000000:
            r.u32()
            ref = v & 0x3FFFFFFF
            obj = objects.get(ref)
            if obj is None or obj[0] != kind:
                raise FormatError(f"bad {kind} reference {ref} at {r.o - 8:#x}")
            return obj[1]
        if v != 1:
            raise FormatError(f"bad {kind} pointer {v:#x} at {r.o - 4:#x}")
        oid = new_id()
        obj = read_inline(oid)
        objects[oid] = (kind, obj)
        return obj

    def read_vb(oid):
        count_off = r.o + 4
        flags, count = r.u32(), r.u32()
        r.tag("VTXD")
        r.u32()
        n = r.u32()
        attribs = [tuple(r.raw(3)) for _ in range(n)]
        r.raw(6)
        for _, typ, _ in attribs:
            if typ not in VTYPES:
                raise FormatError(f"unknown vertex type {typ} at {r.o:#x}")
        stride = max(off + VTYPES[typ][2] for _, typ, off in attribs)
        data_off = r.o
        return VertexBuffer(oid, flags, count, stride, attribs, r.raw(count * stride), count_off, data_off)

    def read_ib(oid):
        count_off = r.o + 4
        flags, count, size = r.u32(), r.u32(), r.u32()
        data_off = r.o
        return IndexBuffer(oid, flags, count, size, r.raw(count * size), count_off, data_off)

    mesh_version = 201
    if tagged:
        r.tag("MESH")
        mesh_version = r.u32()
    parts = []
    num_parts = r.u32()
    for k in range(num_parts):
        new_id()                                   # the part
        if r.u32() != 1:
            raise FormatError(f"part {k}: unexpected stream list at {r.o - 4:#x}")
        start = r.o
        r.tag("RNMS")
        new_id()                                   # the stream list
        r.u32()
        streams = []
        for _ in range(r.u32()):
            vb = pointer("vb", read_vb)
            r.u32()                                # byte offset
            if vb is not None:
                streams.append(vb)
        if r.u32() != 0:
            raise FormatError(f"part {k}: fast-blend buffers not supported ({r.o - 4:#x})")
        ib = pointer("ib", read_ib)
        ib_fields = r.o                            # u32 ibOffset, ibCount, ibBase
        ib_offset, ib_count, ib_base = r.u32(), r.u32(), r.u32()
        prim = r.u16()
        blend_shapes = []
        used_off = r.o
        used = r.u32()
        r.u32()
        skin_map = r.raw(r.u32())
        if r.u32() != 0:
            # blend-shape data (NuDynamicBuffers): not decoded yet. Run the game's serializer on it
            # to find where it ends and how many serialized objects (ids) it registers.
            new_id()                                   # the dynamic buffers object
            end_pos, registered, shapes = _skip_dynamic_buffers(r.b, r.o, mesh_version)
            for _ in range(registered):
                new_id()
            r.o = end_pos
            blend_shapes = shapes
        r.u32()
        bounds_off = r.o
        centre, extents = r.f32(4), r.f32(4)
        r.f32()
        r.u32()
        parts.append(MeshPart(k, streams, ib, ib_offset, ib_count, ib_base, prim, used,
                              skin_map, centre, extents, start, r.o, ib_fields, used_off, bounds_off,
                              blend_shapes))
    return parts


def _vector_len(r: Reader) -> int:
    """EASTL vectors are serialized as u32 id (0 = inline) + u32 size."""
    if r.u32() != 0:
        raise FormatError(f"shared vector reference at {r.o - 4:#x} not supported")
    return r.u32()


def _matrix(r: Reader) -> np.ndarray:
    return np.array(r.f32(16), np.float32).reshape(4, 4)


def _read_skeleton(r: Reader) -> Skeleton:
    """NuCharacterData (HGOL), version >= 8."""
    r.tag("HGOL")
    version = r.u32()
    joints = []
    for _ in range(_vector_len(r)):
        name = r.str16()
        orient = _matrix(r)
        offset = r.f32(3)
        parent = r.u8()
        flags = r.u8()
        joints.append(Joint(name, orient, offset, -1 if parent == 0xFF else parent, flags))
    local = [_matrix(r) for _ in range(_vector_len(r))]
    inv_world = [_matrix(r) for _ in range(_vector_len(r))]
    r.raw(_vector_len(r))                              # m_JointIxs
    pois = []
    for _ in range(_vector_len(r)):
        name = r.str16()
        pois.append((name, _matrix(r), r.u8()))
    r.raw(_vector_len(r))                              # m_PoiIxs
    r.raw(r.u32())                                     # string buffer
    meta = []
    for _ in range(_vector_len(r)):
        t, j, s = r.u8(), r.u8(), r.u16()
        meta.append(LayerMeta(t, -1 if j == 0xFF else j, s, r.u8() if version >= 8 else 0))
    layers = []
    for _ in range(_vector_len(r)):
        layers.append(Layer(r.str16(), r.u16(), r.u16(), r.u16()))
    return Skeleton(joints, local, inv_world, pois, meta, layers)


def _scan_materials(b: bytes, start: int):
    """Heuristic scan of UMTL (NuMtlSceneBlock): material names and .nut texture names.

    NuMtl records are large and heavily versioned; until they are decoded
    properly, names are located as '01 00' + str16 in index order. The result is
    only returned when the number of names equals the material count.
    """
    import re
    version, count = struct.unpack_from(">II", b, start + 4)
    end = b.find(b"SUPC", start)
    end = len(b) if end < 0 else end
    names = []
    for m in re.finditer(rb"\x01\x00\x00([\x02-\x7f])([\x20-\x7e]{1,126})\x00", b[start:end]):
        n = m.group(2)
        if m.group(1)[0] == len(n) + 1 and b":VARIANT" not in n and not n.endswith(b".nut"):
            names.append((start + m.start(), n.decode("latin-1")))
    if len(names) != count:
        return count, None
    out = []
    for i, (off, name) in enumerate(names):
        nxt = names[i + 1][0] if i + 1 < len(names) else end
        texs = []
        for t in re.finditer(rb"\x00([\x04-\x7f])([\x20-\x7e]{3,126}\.nut)\x00", b[off:nxt]):
            base = t.group(2).decode("latin-1").rsplit("/", 1)[-1]
            if base not in texs:
                texs.append(base)
        out.append((name, texs))
    return count, out


def _read_display(r: Reader) -> tuple[list, list]:
    """NuDisplayScene (DISP), version >= 0x22: clip objects and specials."""
    r.tag("DISP")
    version = r.u32()
    if version < 0x22:
        raise FormatError(f"DISP version {version:#x} not supported")
    clip_objects = []
    for _ in range(_vector_len(r)):
        items = []
        for _ in range(r.u16()):
            material, _, lightmap, transform, mesh = (r.u16() for _ in range(5))
            lt, tt, gt = r.u8(), r.u8(), r.u8()
            if version >= 0x23:
                r.u8()
            r.u8()
            r.u8()
            items.append(ClipItem(material, transform, lightmap, mesh, lt, tt, gt))
        clip_objects.append(items)
    specials = []
    for _ in range(_vector_len(r)):
        name = r.str16()
        mtx = _matrix(r)
        mn, mx, sph = r.f32(4), r.f32(4), r.f32(4)
        clip, flags = r.u32(), r.u32()
        r.raw(4 * _vector_len(r))                      # clip ranges
        inst, anim = r.u32(), r.u32()
        r.u16()
        r.u16()
        specials.append(Special(name, mtx, mn, mx, sph, clip, flags, inst, anim))
    return clip_objects, specials


def read_model(path: str) -> Model:
    with open(path, "rb") as f:
        raw = f.read()
    res = parse_resource(raw, path)
    b = res.body
    ntbl = b.find(b"LBTN")
    size, = struct.unpack_from(">I", b, ntbl + 8)
    model = Model(path, res.source_path, b[ntbl + 12:ntbl + 12 + size])

    mesh = b.find(b"HSEM")
    if mesh < 0:
        raise FormatError(f"{path}: no MESH block")
    model.parts = _read_parts(Reader(b, mesh))

    umtl = b.find(b"LTMU")
    if umtl >= 0:
        model.num_materials, model.materials = _scan_materials(b, umtl)

    disp = b.find(b"PSID")
    if disp >= 0:
        model.clip_objects, model.specials = _read_display(Reader(b, disp))

    off = b.find(b"LOGH")
    while off >= 0:
        model.skeletons.append(_read_skeleton(Reader(b, off)))
        off = b.find(b"LOGH", off + 4)
    return model
