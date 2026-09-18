"""Pixel formats, DDS read/write and decoding to RGBA."""
import struct
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PixelFormat:
    name: str
    dxgi: int
    block_bytes: int    # bytes per block (or per pixel for uncompressed)
    block_dim: int      # 4 for BCn, 1 for uncompressed


BC1 = PixelFormat("BC1", 71, 8, 4)
BC2 = PixelFormat("BC2", 74, 16, 4)
BC3 = PixelFormat("BC3", 77, 16, 4)
BC4 = PixelFormat("BC4", 80, 8, 4)
BC5 = PixelFormat("BC5", 83, 16, 4)
BC6H = PixelFormat("BC6H", 95, 16, 4)
BC7 = PixelFormat("BC7", 98, 16, 4)
RGBA8 = PixelFormat("RGBA8", 28, 4, 1)
BGRA8 = PixelFormat("BGRA8", 87, 4, 1)
R16 = PixelFormat("R16", 57, 2, 1)
R8 = PixelFormat("R8", 61, 1, 1)
RGBA16F = PixelFormat("RGBA16F", 10, 8, 1)

BY_DXGI = {f.dxgi: f for f in (BC1, BC2, BC3, BC4, BC5, BC6H, BC7, RGBA8, BGRA8, R16, R8, RGBA16F)}
BY_DXGI.update({72: BC1, 75: BC2, 78: BC3, 99: BC7, 96: BC6H, 81: BC4, 84: BC5, 29: RGBA8, 91: BGRA8})
BY_FOURCC = {b"DXT1": BC1, b"DXT3": BC2, b"DXT5": BC3, b"ATI1": BC4, b"BC4U": BC4,
             b"ATI2": BC5, b"BC5U": BC5}


def level_size(fmt: PixelFormat, w: int, h: int, d: int = 1) -> int:
    bw = max(1, (w + fmt.block_dim - 1) // fmt.block_dim)
    bh = max(1, (h + fmt.block_dim - 1) // fmt.block_dim)
    return bw * bh * d * fmt.block_bytes


def surface_size(fmt: PixelFormat, w: int, h: int, mips: int, depth: int = 1,
                 layers: int = 1, volume: bool = False) -> int:
    total = 0
    for m in range(mips):
        d = max(1, depth >> m) if volume else 1
        total += level_size(fmt, max(1, w >> m), max(1, h >> m), d)
    return total * layers


# --- writing -----------------------------------------------------------------

DDSD_CAPS, DDSD_HEIGHT, DDSD_WIDTH, DDSD_PIXELFORMAT = 0x1, 0x2, 0x4, 0x1000
DDSD_MIPMAPCOUNT, DDSD_LINEARSIZE, DDSD_DEPTH = 0x20000, 0x80000, 0x800000
DDSCAPS_TEXTURE, DDSCAPS_MIPMAP, DDSCAPS_COMPLEX = 0x1000, 0x400000, 0x8
DDSCAPS2_CUBEMAP_ALL, DDSCAPS2_VOLUME = 0xFE00, 0x200000
DDPF_FOURCC = 0x4


def build_dds(fmt: PixelFormat, w: int, h: int, mips: int, data: bytes,
              depth: int = 1, cube: bool = False, volume: bool = False,
              array_size: int = 1) -> bytes:
    """Write a DX10-extended DDS (readable by texconv, Blender, Photoshop plugins, etc)."""
    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_MIPMAPCOUNT
    caps = DDSCAPS_TEXTURE | (DDSCAPS_MIPMAP | DDSCAPS_COMPLEX if mips > 1 else 0)
    caps2 = 0
    if cube:
        caps |= DDSCAPS_COMPLEX
        caps2 |= DDSCAPS2_CUBEMAP_ALL
    if volume:
        flags |= DDSD_DEPTH
        caps |= DDSCAPS_COMPLEX
        caps2 |= DDSCAPS2_VOLUME
    pf = struct.pack("<II4s20x", 32, DDPF_FOURCC, b"DX10")
    hdr = struct.pack("<4sIIIIIII44x", b"DDS ", 124, flags, h, w, 0,
                      depth if volume else 0, mips) + pf + struct.pack("<II12x", caps, caps2)
    dim = 4 if volume else 3
    dx10 = struct.pack("<IIIII", fmt.dxgi, dim, 0x4 if cube else 0, array_size, 0)
    return hdr + dx10 + data


# --- reading -----------------------------------------------------------------

@dataclass
class DDSInfo:
    fmt: PixelFormat | None
    width: int
    height: int
    depth: int
    mips: int
    faces: int
    array_size: int
    header_size: int
    fourcc: bytes

    @property
    def data_size(self) -> int:
        if self.fmt is None:
            return 0
        return surface_size(self.fmt, self.width, self.height, self.mips, self.depth,
                            self.faces * self.array_size, volume=self.depth > 1)


def parse_dds_header(data: bytes, off: int = 0) -> DDSInfo:
    if data[off:off + 4] != b"DDS ":
        raise ValueError("not a DDS")
    (flags, h, w, _linear, depth, mips) = struct.unpack_from("<IIIIII", data, off + 8)
    pf_flags, cc, bitcount, rmask, gmask, bmask, amask = struct.unpack_from("<I4sIIIII", data, off + 80)
    caps2, = struct.unpack_from("<I", data, off + 112)
    faces = 6 if caps2 & 0x200 else 1
    header_size, array_size, fmt = 128, 1, None
    mips = max(1, mips)
    depth = depth if (caps2 & DDSCAPS2_VOLUME) else 1
    if pf_flags & DDPF_FOURCC:
        if cc == b"DX10":
            dxgi, _dim, misc, array_size, _ = struct.unpack_from("<IIIII", data, off + 128)
            header_size = 148
            fmt = BY_DXGI.get(dxgi)
            if misc & 0x4:
                faces = 6
        else:
            fmt = BY_FOURCC.get(cc)
    elif bitcount == 32:
        fmt = RGBA8 if rmask == 0xFF else BGRA8
    elif bitcount == 8:
        fmt = R8
    return DDSInfo(fmt, w, h, max(1, depth), mips, faces, max(1, array_size), header_size, cc)


def decode_rgba(fmt: PixelFormat, data: bytes, w: int, h: int) -> np.ndarray:
    """Decode the top mip level of one surface to an (h, w, 4) uint8 array."""
    import texture2ddecoder as t2d
    n = level_size(fmt, w, h)
    buf = bytes(data[:n])
    if fmt.block_dim == 4:
        fn = getattr(t2d, "decode_" + fmt.name.lower().rstrip("h"), None)
        if fn is None:
            raise NotImplementedError(f"no decoder for {fmt.name}")
        bgra = np.frombuffer(fn(buf, w, h), np.uint8).reshape(h, w, 4)
        rgba = bgra[..., [2, 1, 0, 3]].copy()
        if fmt.name == "BC4":
            rgba[..., 1] = rgba[..., 2] = rgba[..., 0]
        if fmt.name == "BC5":
            # BC5 stores X/Y; rebuild Z so normal maps look right.
            x = rgba[..., 0] / 127.5 - 1
            y = rgba[..., 1] / 127.5 - 1
            rgba[..., 2] = ((np.sqrt(np.clip(1 - x * x - y * y, 0, 1)) + 1) * 127.5).astype(np.uint8)
        return rgba
    a = np.frombuffer(buf, np.uint8)
    if fmt is RGBA8:
        return a.reshape(h, w, 4).copy()
    if fmt is BGRA8:
        return a.reshape(h, w, 4)[..., [2, 1, 0, 3]].copy()
    if fmt is R16:
        g = (np.frombuffer(buf, "<u2").reshape(h, w) >> 8).astype(np.uint8)
    elif fmt is R8:
        g = a.reshape(h, w)
    else:
        raise NotImplementedError(fmt.name)
    return np.dstack([g, g, g, np.full_like(g, 255)])
