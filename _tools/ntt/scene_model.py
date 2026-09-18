"""Scene models (.MODEL, 'GSC2' / NuScene2): level geometry and props placed by SCENE_BAKED files.

Layout (NuScene2::Serialize 0x140203f00, traced into _tools/traces/NuScene2*.txt):
    materials: u32 n, n x (str16 object id, str16 .material resource path, str16 slot name)
    meshes:    u32 id, u32 size, u32 n, n x mesh-part pointer (same RNMS/VTXD parts as NU20 MESH)
    m_transforms: vector<mtx>
    clip objects: vector<NuClipObject> (u16 numItems, items: u16 material, u16 transform,
                  u16 lightmap, u16 transform, u16 mesh, u8 x4, bool requiresLightState, bool isFaceon)
    nodes:     vector (m_name, joint index, local bounds, vector<(u32 modelIndex, u32 distance)> per LOD,
               m_initialTransform, fade/lod settings, drawMesh, castsLiveShadows ...)
    lightmap blocks, clip item UV scale/offset, ...

Mesh parts are parsed natively; everything else is decoded by emulating the game's own
serializer (see emu.py) with the part loader short-circuited to our parsed byte ranges.
"""
import os
import struct
import sys
from dataclasses import dataclass, field

import numpy as np

from . import model as M
from .resource import read_resource

_TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

NUSCENE2_SERIALIZE = 0x140203f00
MESH_PART_SERIALIZE = 0x14340eb40
NONE = 0xFFFFFFFF


@dataclass
class ClipItem:
    material: int
    transform: int
    lightmap: int
    mesh: int


@dataclass
class Node:
    name: str
    models: list = field(default_factory=list)      # clip object index per LOD
    transform: np.ndarray = None
    draw: bool = True
    fields: dict = field(default_factory=dict)


@dataclass
class SceneModel:
    path: str
    materials: list          # (resource path, slot name)
    parts: list              # model.MeshPart
    transforms: list         # 4x4 row-vector matrices
    clip_objects: list       # [ClipItem]
    nodes: list              # Node

    def visible_nodes(self):
        """Top LOD, drawable nodes (skips _LODn, shadow and occluder copies)."""
        out = []
        for n in self.nodes:
            low = n.name.lower()
            if not n.draw or not n.models:
                continue
            if "_lod" in low and low.rsplit("_lod", 1)[1].isdigit():
                continue
            out.append(n)
        return out


_emu = None


def _mtx(val):
    if isinstance(val, list) and len(val) == 16:
        if all(isinstance(v, int) for v in val):
            val = [struct.unpack("<f", struct.pack("<I", v))[0] for v in val]
        return np.array(val, np.float32).reshape(4, 4)
    return None


def read_scene_model(path: str) -> SceneModel:
    global _emu
    import emu as E
    import fieldlog as FL
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RIP, UC_X86_REG_RSP

    body = read_resource(path).body
    start = body.find(b"2CSG")
    if start < 0:
        raise M.FormatError(f"{path}: no GSC2 chunk")
    sm = body.find(b"SMNR", start)
    parts = M._read_parts(M.Reader(body, sm - 8), tagged=False) if sm >= 0 else []
    ends = {p.start: p.end for p in parts}

    # engine globals (string tables, resource registry) are lazily allocated on the emulated heap,
    # so the heap must not be rewound between models; start a fresh emulator when it fills up
    if _emu is None or _emu.heap_ptr - E.HEAP > E.HEAP_SIZE * 0.8:
        _emu = E.Emu()
    emu = _emu
    stream = E.Stream(emu, body, start)
    ser = E.make_serializer(emu, stream, 0)
    log = FL.FieldLog(emu, stream)
    bad = []

    def skip_part(mu, a, sz, u):
        if stream.pos not in ends:
            bad.append(stream.pos)
            mu.emu_stop()
            return
        stream.pos = ends[stream.pos]
        rsp = mu.reg_read(UC_X86_REG_RSP)
        ret = struct.unpack("<Q", mu.mem_read(rsp, 8))[0]
        mu.reg_write(UC_X86_REG_RSP, rsp + 8)
        mu.reg_write(UC_X86_REG_RAX, 1)
        mu.reg_write(UC_X86_REG_RIP, ret)

    hook = emu.mu.hook_add(UC_HOOK_CODE, skip_part, begin=MESH_PART_SERIALIZE, end=MESH_PART_SERIALIZE)
    try:
        emu.call(NUSCENE2_SERIALIZE, [emu.alloc(0x2000), ser])
    finally:
        log.flush()
        emu.mu.hook_del(hook)
        log.detach()
    if bad:
        raise M.FormatError(f"{path}: mesh part at unexpected offset {bad[0]:#x}")

    # nested primitives log the same read twice; the later entry holds the value
    values = []
    for v in log.values:
        if values and values[-1][0] == v[0] and values[-1][1] == v[1]:
            values[-1] = v
        else:
            values.append(v)

    materials, transforms, clips, nodes = [], [], [], []
    res_path = None
    stage = "materials"
    item = None
    for pos, name, kind, val in values:
        if name == "resourceIDAsString":
            res_path = val
        elif name == "m_materialSlots[i].name":
            materials.append((res_path, val))
        elif name == "meshes_size":
            stage = "transforms"
        elif stage == "transforms" and name == "" and _mtx(val) is not None:
            transforms.append(_mtx(val))
        elif name == "m_numItems":
            stage = "clips"
            clips.append([])
        elif name == "m_items[i].materialIndex":
            item = [val]
        elif name.startswith("m_items[i].") and item is not None and len(item) < 5 and kind == "u16":
            item.append(val)
            if len(item) == 5:
                clips[-1].append(ClipItem(item[0], item[1], item[2], item[4]))
        elif name == "m_name":
            stage = "nodes"
            nodes.append(Node(val))
        elif stage == "nodes" and nodes:
            n = nodes[-1]
            if name == "modelIndex":
                if val != NONE:
                    n.models.append(val)
            elif name == "m_initialTransform":
                n.transform = _mtx(val)
            elif name == "drawMesh":
                n.draw = bool(val)
            elif name and kind != "str":
                n.fields.setdefault(name, val)
    return SceneModel(path, materials, parts, transforms, clips, nodes)
