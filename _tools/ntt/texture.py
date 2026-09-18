"""Textures: .TEXTURE (RTXT), .TEX (plain DDS) and .NXG_TEXTURES (TSXT bundles).

.TEXTURE body:
    u32 hash, u32 size, '.CC4' 'HSER' 'RTXT'
    u32 version (12..20), u32 width, u32 height, u32 depth, u32 mips,
    u32 kind (1=2D, 2=volume, 3=cube, 4=array), u32 format
    ... version-dependent fields (guid etc) ...
    pixel data (all mips of all surfaces), which runs to the end of the file

NXG_TEXTURES body: a TSXT table naming each texture (either an external
`.TEX` texture-page reference or an embedded `.nut` image), followed by the
embedded DDS files back to back.
"""
import re
import struct
from dataclasses import dataclass

from . import dds
from .resource import parse_resource

NTT_FORMATS = {
    1: dds.BC1, 2: dds.BC1, 6: dds.BC3, 7: dds.BGRA8, 30: dds.BC6H,
    31: dds.BC7, 36: dds.R16, 37: dds.BC4, 107: dds.BC5,
}
KIND_2D, KIND_VOLUME, KIND_CUBE, KIND_ARRAY = 1, 2, 3, 4


@dataclass
class Texture:
    name: str
    fmt: dds.PixelFormat
    width: int
    height: int
    depth: int
    mips: int
    kind: int
    data: bytes

    def to_dds(self) -> bytes:
        return dds.build_dds(self.fmt, self.width, self.height, self.mips, self.data,
                             depth=self.depth, cube=self.kind == KIND_CUBE,
                             volume=self.kind == KIND_VOLUME,
                             array_size=self.depth if self.kind == KIND_ARRAY else 1)

    def to_rgba(self):
        return dds.decode_rgba(self.fmt, self.data, self.width, self.height)


def read_texture(path: str) -> Texture:
    with open(path, "rb") as f:
        raw = f.read()
    res = parse_resource(raw, path)
    body = res.body
    i = body.find(b"RTXT")
    if i < 0:
        raise ValueError(f"{path}: no RTXT chunk")
    version, w, h, depth, mips, kind, fmt_id = struct.unpack_from(">7I", body, i + 4)
    fmt = NTT_FORMATS.get(fmt_id)
    if fmt is None:
        raise NotImplementedError(f"{path}: texture format {fmt_id} (version {version})")
    mips = max(1, mips)
    if kind == KIND_VOLUME:
        size = dds.surface_size(fmt, w, h, mips, depth, volume=True)
    elif kind in (KIND_CUBE, KIND_ARRAY):
        size = dds.surface_size(fmt, w, h, mips, layers=depth)
    else:
        size = dds.surface_size(fmt, w, h, mips)
    header_len = len(body) - (i + 4) - size
    if not 20 <= header_len <= 256:
        raise ValueError(f"{path}: size mismatch (fmt {fmt_id} {w}x{h}x{depth} mips {mips} "
                         f"kind {kind}, header would be {header_len} bytes)")
    return Texture(res.source_path, fmt, w, h, depth, mips, kind, body[len(body) - size:])


@dataclass
class NxgEntry:
    name: str
    external: bool      # True: reference to another file, no pixels here
    dds: bytes | None


_NAME_RE = re.compile(rb"[\x20-\x7e]{4,}\.(?:nut|tex|dds)\x00", re.IGNORECASE)


def _table_names(table: bytes) -> list[str]:
    """Entry names are stored as u16 BE length (including NUL) + string."""
    names = []
    for m in _NAME_RE.finditer(table):
        end = m.end()
        for start in range(m.start(), min(m.start() + 3, end)):
            if start >= 2 and struct.unpack_from(">H", table, start - 2)[0] == end - start:
                names.append(table[start:end - 1].decode("latin-1"))
                break
    return names


def read_nxg_textures(path: str) -> list[NxgEntry]:
    with open(path, "rb") as f:
        raw = f.read()
    body = parse_resource(raw, path).body
    first_dds = body.find(b"DDS |")
    names = _table_names(body if first_dds < 0 else body[:first_dds])

    blobs, off = [], first_dds
    while off >= 0 and body[off:off + 4] == b"DDS ":
        info = dds.parse_dds_header(body, off)
        if info.width == 0 or info.height == 0:
            break   # stub entry: pixels live in another file
        end = off + info.header_size + info.data_size if info.fmt else -1
        if info.fmt is None or end > len(body):
            end = body.find(b"DDS |", off + 4)
            end = len(body) if end < 0 else end
        blobs.append(body[off:end])
        off = end

    entries, k = [], 0
    for n in names:                      # keep table order: texture ids index this list
        if n.lower().endswith(".tex"):
            entries.append(NxgEntry(n, True, None))
        else:
            entries.append(NxgEntry(n, False, blobs[k] if k < len(blobs) else None))
            k += 1
    for extra in blobs[k:]:
        entries.append(NxgEntry(f"unnamed_{len(entries)}.dds", False, extra))
    return entries
