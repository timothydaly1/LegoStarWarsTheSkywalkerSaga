"""Per-instance vertex colours (.INSTANCE_VERTEX_COLOURS, 'INVC').

A scene instance (ApiRenderModel "Vertex Colours Resource") can carry its own baked vertex
colours - lighting and ambient occlusion burnt into the model's vertices for that placement.

    'INVC' u32 version (207), u32 numBuffers, then per mesh part:
        u32 1, u32 1, [GUID16 from the second buffer on], u32 flags (0x512), u32 count,
        'VTXD' u32 version, u32 numAttribs, attribs (semantic 2 = colour, type 9 = RGBA bytes),
        6 bytes, count x 4 bytes of colour

Buffers are in mesh-part order and only apply when their counts match the model's parts, since
bakes are tied to the model version they were made from.
"""
import struct

import numpy as np

from . import model as M
from .resource import read_resource


def read_instance_colours(path: str) -> list:
    """-> [RGBA uint8 array per mesh part]"""
    body = read_resource(path).body
    out = []
    o = body.find(b"DXTV")
    while o >= 0:
        count = struct.unpack_from(">I", body, o - 4)[0]
        r = M.Reader(body, o)
        r.tag("VTXD")
        r.u32()
        attribs = [tuple(r.raw(3)) for _ in range(r.u32())]
        r.raw(6)
        stride = max(off + M.VTYPES[typ][2] for _, typ, off in attribs)
        data = np.frombuffer(r.raw(count * stride), np.uint8).reshape(count, stride)
        sem = {s: (o2, M.VTYPES[t][2]) for s, t, o2 in attribs}
        off, size = sem.get(M.COLOR0, (0, 4))
        out.append(np.ascontiguousarray(data[:, off:off + min(size, 4)]))
        o = body.find(b"DXTV", r.o)
    return out


def matches(colours: list, parts: list) -> bool:
    """True when the bake belongs to this model version (one buffer per part, same vertex counts)."""
    return bool(colours) and len(colours) <= len(parts) and \
        all(len(c) == p.streams[0].count for c, p in zip(colours, parts) if p.streams)
