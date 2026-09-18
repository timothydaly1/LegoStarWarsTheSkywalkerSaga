"""Compressed curve animation (NuAnimHeader 'ANIx') as embedded in .AN4 files.

Recovered from the game's sampler (0x14362b9e0) and key decoders
(0x14362d300 type 6, 0x14362cdb0 type 7). Header (endianness = file endianness,
'ANIE' big-endian / 'EINA' little-endian), offsets relative to header start:

    +0x00 u32  version 'ANIx'
    +0x04 u16  numNodes
    +0x06 u16  numFrames
    +0x08 u16  curveGroupSize     bytes of curve data per 4-frame block
    +0x0c u16  numCurves          per node (6: posX posY posZ, rotX rotY rotZ)
    +0x10 u8   endFrames
    +0x11 u8   numShortIntegers
    +0x12 u8   fixedUp flags
    +0x13 u8   miscFlags          0x20: key type words carry a 'no interpolation' bit 15
                                  0x10: float constant table follows the shorts
    +0x14 u16  ?, +0x16 u16 totalNumFrames
    +0x1c f32  constantBase, +0x20 f32 constantScale
    +0x24 i32  -> (scale, min) f32 pairs, one per decoded curve
    +0x28 i32  -> constants (u16 table)
    +0x2c i32  -> key types, u16 per node*curve
    +0x30 i32  -> curve block data
    +0x3c i32  -> child animations (version >= 'ANI8'?)

Key types (masked to 15 bits when miscFlags & 0x20):
    6   u32 per block: low byte = value, 4 x 6-bit weights toward the next block's value
    7   8 bytes per block: u16 value + 4 packed 12-bit weights (/4095)
    2   rotation: u32 per frame, "smallest three" 10-bit quaternion with 4 (scale, min) pairs
    4   rotation: constant packed quaternion (u32 in the min slot of a (scale, min) pair)
    8   u8 per frame -> signed short constant table
    11  f32 per frame
    14  0.0   15  1.0
    other: constant = key * constantScale + constantBase
Curves 0..2 are translation; curves 3..5 are Euler angles combined into a quaternion.
"""
import math
import struct
from dataclasses import dataclass

import numpy as np

MAGICS = (b"ANIE", b"ANID", b"ANIA", b"ANIB", b"ANIC")


@dataclass
class Clip:
    num_nodes: int
    num_frames: int
    rotations: np.ndarray      # (frames, nodes, 4) quaternion x,y,z,w
    translations: np.ndarray   # (frames, nodes, 3)
    key_types: np.ndarray      # (nodes, curves)


def euler_values(clip_vals):
    return clip_vals


def euler_to_quat(x, y, z):
    """Matches the engine helper 0x1436214a0."""
    cx, cy, cz = math.cos(x * 0.5), math.cos(y * 0.5), math.cos(z * 0.5)
    sx, sy, sz = math.sin(x * 0.5), math.sin(y * 0.5), math.sin(z * 0.5)
    qx = cx * sy * sz - sx * cy * cz
    qy = cx * sy * cz + sx * cy * sz
    qz = sx * sy * cz - cx * cy * sz
    qw = cx * cy * cz + sx * sy * sz
    return qx, qy, qz, qw


def unpack_quat_scaled(v: int, scales, mins):
    """0x1436146c0: 2-bit dropped index, three 10-bit components with per-component scale/min."""
    a, b, c, drop = (v >> 20) & 0x3FF, (v >> 10) & 0x3FF, v & 0x3FF, v >> 30
    idx = [i for i in range(4) if i != drop]
    q = [0.0] * 4
    for comp, raw in zip(idx, (a, b, c)):
        q[comp] = raw * scales[comp] + mins[comp]
    q[drop] = math.sqrt(max(0.0, 1.0 - sum(x * x for x in q)))
    return q


def unpack_quat_const(v: int):
    """0x143614590 (constants are initialised at runtime; standard 10-bit +-1/sqrt2 mapping)."""
    if v == 0xE0080200:
        return [0.0, 0.0, 0.0, 1.0]
    k = math.sqrt(2.0) / 1023.0
    e = [((v >> 20) & 0x3FF) * k - 0.70710678, ((v >> 10) & 0x3FF) * k - 0.70710678, (v & 0x3FF) * k - 0.70710678]
    w = math.sqrt(max(0.0, 1.0 - sum(x * x for x in e)))
    drop = v >> 30
    return e[:drop] + [w] + e[drop:]


def find_headers(data: bytes):
    out = []
    for magic in MAGICS:
        for endian, tag in ((">", magic), ("<", magic[::-1])):
            i = data.find(tag)
            while i >= 0:
                out.append((i, endian))
                i = data.find(tag, i + 4)
    return sorted(out)


ROT_FIRST = False      # experiment: curves 0-2 rotation, 3-5 translation


def decode_clip(data: bytes, base: int, endian: str) -> Clip:
    E = endian
    u16 = lambda o: struct.unpack_from(E + "H", data, o)[0]
    u32 = lambda o: struct.unpack_from(E + "I", data, o)[0]
    i32 = lambda o: struct.unpack_from(E + "i", data, o)[0]
    f32 = lambda o: struct.unpack_from(E + "f", data, o)[0]

    nodes, frames, group, curves = u16(base + 4), u16(base + 6), u16(base + 8), u16(base + 0xC)
    num_short, misc = data[base + 0x11], data[base + 0x13]
    cbase, cscale = f32(base + 0x1C), f32(base + 0x20)
    o_scalemin, o_const, o_types, o_blocks = (base + i32(base + k) for k in (0x24, 0x28, 0x2C, 0x30))
    high_bit = bool(misc & 0x20)
    float_consts = None
    if misc & 0x10:
        float_consts = ((o_const + num_short * 2 + 3) & ~3) - 0x40

    kt_raw = np.array([u16(o_types + 2 * k) for k in range(nodes * curves)], np.uint16).reshape(nodes, curves)
    kts = kt_raw & 0x7FFF if high_bit else kt_raw

    def constant(k):
        if high_bit:
            return k * cscale + cbase
        if float_consts is not None:
            return f32(float_consts + 4 * k)
        return u16(o_const + 2 * k - 0x20) * cscale + cbase

    rot = np.zeros((frames, nodes, 4), np.float32)
    pos = np.zeros((frames, nodes, 3), np.float32)
    for f in range(frames):
        block, idx = f >> 2, f & 3
        cur = o_blocks + block * group
        sm = o_scalemin
        for n in range(nodes):
            vals = [0.0] * curves
            quat = None
            c = 0
            while c < curves:
                k = int(kts[n, c])
                v = 0.0
                if k == 14:
                    v = 0.0
                elif k == 15:
                    v = 1.0
                elif k == 6:
                    word = u32(cur)
                    nxt = u32(cur + group) & 0xFF
                    frac = ((word >> 8) >> (6 * idx) & 0x3F) * 0.015625
                    v = ((nxt - (word & 0xFF)) * frac + (word & 0xFF)) * f32(sm) + f32(sm + 4)
                    cur += 4
                    sm += 8
                elif k == 7:
                    start, nxt = u16(cur), u16(cur + group)
                    w2, w4, w6 = u16(cur + 2), u16(cur + 4), u16(cur + 6)
                    if idx == 0:
                        frac = w2 & 0xFFF
                    elif idx == 1:
                        frac = w4 & 0xFFF
                    elif idx == 2:
                        frac = w6 & 0xFFF
                    else:
                        frac = ((((w6 & 0xF00F) | data[cur + 3]) >> 4) | (data[cur + 5] & 0xF0)) & 0xFFFF
                    v = (frac / 4095.0 * (nxt - start) + start) * f32(sm) + f32(sm + 4)
                    cur += 8
                    sm += 8
                elif k == 8:
                    b = data[cur + idx]
                    v = float(struct.unpack_from(E + "h", data, o_const + 2 * b)[0])
                    cur += 4
                elif k == 11:
                    v = f32(cur + 4 * idx)
                    cur += 16
                elif k == 2 and c == (0 if ROT_FIRST else 3):
                    scales = [f32(sm + 8 * i) for i in range(4)]
                    mins = [f32(sm + 8 * i + 4) for i in range(4)]
                    quat = unpack_quat_scaled(u32(cur + 4 * idx), scales, mins)
                    cur += 16
                    sm += 32
                    c += 3
                    continue
                elif k == 4 and c == (0 if ROT_FIRST else 3):
                    quat = unpack_quat_const(u32(sm + 4))
                    sm += 8
                    c += 3
                    continue
                elif k in (2, 4, 10):
                    raise NotImplementedError(f"key type {k} (node {n} curve {c})")
                else:
                    v = constant(k)
                vals[c] = v
                c += 1
            if ROT_FIRST:
                pos[f, n] = vals[3:6] if curves >= 6 else (0, 0, 0)
                rot[f, n] = quat if quat is not None else euler_to_quat(vals[0], vals[1], vals[2])
            else:
                pos[f, n] = vals[0:3]
                if quat is not None:
                    rot[f, n] = quat
                elif curves >= 6:
                    rot[f, n] = euler_to_quat(vals[3], vals[4], vals[5])
                else:
                    rot[f, n] = (0, 0, 0, 1)
    return Clip(nodes, frames, rot, pos, kts)
