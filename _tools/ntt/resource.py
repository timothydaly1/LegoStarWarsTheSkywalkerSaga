"""The resource container every NTT asset starts with.

Layout (big-endian):
    u32  header_size           # size of the resource header; the asset body follows it
    tag  '.CC4'                # FourCCs are stored byte-reversed on disk ('4CC.')
    tag  'HSER' 'HSER'         # 'RESH' resource header
    u32  version
    u16  path_len, path (NUL-terminated)
    16B  guid
    ...  dependency / provenance data (varies by version)

Nested chunks inside bodies use the same convention: u32 size (big-endian,
including the 8-byte chunk header) followed by a reversed FourCC.
"""
import struct
import uuid
from dataclasses import dataclass


def fourcc(b: bytes) -> str:
    """Decode an on-disk (reversed) FourCC."""
    return b[::-1].decode("latin-1")


@dataclass
class Resource:
    path: str           # file on disk
    version: int
    source_path: str    # engine-side path stored in the header
    guid: uuid.UUID
    header: bytes
    body: bytes


def read_resource(path: str) -> Resource:
    with open(path, "rb") as f:
        data = f.read()
    return parse_resource(data, path)


def parse_resource(data: bytes, path: str = "") -> Resource:
    header_size, = struct.unpack_from(">I", data, 0)
    if data[4:8] != b".CC4" or data[8:12] != b"HSER":
        raise ValueError(f"{path}: not an NTT resource")
    version, name_len = struct.unpack_from(">IH", data, 16)
    name = data[22:22 + name_len].split(b"\0", 1)[0].decode("latin-1")
    guid_off = 22 + name_len
    guid = uuid.UUID(bytes=data[guid_off:guid_off + 16])
    return Resource(path, version, name, guid, data[:header_size], data[header_size:])


def iter_chunks(data: bytes, offset: int = 0, end: int | None = None):
    """Yield (offset, tag, size) for a run of size+FourCC chunks.

    Stops at the first thing that does not look like a chunk.
    """
    end = len(data) if end is None else end
    while offset + 8 <= end:
        size, = struct.unpack_from(">I", data, offset)
        tag = data[offset + 4:offset + 8]
        if size < 8 or offset + size > end or not all(32 <= c < 127 for c in tag):
            return
        yield offset, fourcc(tag), size
        offset += size
