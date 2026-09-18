"""Baked reflection archives (.PREFAB_BAKED, .SCENE_BAKED, .GRAPH_BAKED ...).

Self-describing little-endian format:
    record  = u32 size (includes itself) + u32 nameLen + name + payload
    TypeList: u32 n, n x record 'Type' (str name, i32 byteSize or -1)
    ClassList: u32 n, n x record 'Class' (str name, record 'Version' f32,
               record 'Types' (u8, u32 nFields, fields x [u32 type, str name, i32 a, u32 b,
               u32 flags, u32 c, i32 d]))
    OLST: objects ('MOBJ' records)

Field type numbers index the TypeList for plain fields and the ClassList for
class-typed fields (flags & 0x80000000).
"""
import re
import struct
from dataclasses import dataclass, field

RESOURCE_PATH = re.compile(rb"[A-Za-z0-9_][A-Za-z0-9_/\\\-. #$]*\.[A-Za-z0-9_]{2,16}")


def _u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def _str(b, o):
    n = _u32(b, o)
    return b[o + 4:o + 4 + n].split(b"\0", 1)[0].decode("latin-1"), o + 4 + n


def record(b, o):
    """-> (name, payload offset, end offset)"""
    size = _u32(b, o)
    name, p = _str(b, o + 4)
    return name, p, o + size


@dataclass
class Field:
    type: int
    name: str
    a: int
    b: int
    flags: int
    c: int
    d: int

    @property
    def is_base(self):
        return self.flags & 0xC0000000 == 0xC0000000

    @property
    def is_class(self):
        return bool(self.flags & 0x80000000)


@dataclass
class ClassDef:
    name: str
    version: float
    flag: int
    fields: list = field(default_factory=list)


@dataclass
class Archive:
    types: list          # (name, size)
    classes: list        # ClassDef
    body: bytes
    olst: int            # offset of OLST record


def read_archive(data: bytes) -> Archive:
    header, = struct.unpack_from(">I", data, 0)
    b = data[header:]
    t = b.find(b"TypeList\0") - 8
    name, p, end = record(b, t)
    n = _u32(b, p)
    p += 4
    types = []
    for _ in range(n):
        _, q, e = record(b, p)
        tname, q = _str(b, q)
        types.append((tname, struct.unpack_from("<i", b, q)[0]))
        p = e
    name, p, cend = record(b, end)
    assert name == "ClassList", name
    n = _u32(b, p)
    p += 4
    classes = []
    for _ in range(n):
        _, q, e = record(b, p)
        cname, q = _str(b, q)
        _, vq, ve = record(b, q)
        ver = struct.unpack_from("<f", b, vq)[0]
        _, tq, te = record(b, ve)
        # two header shapes: u8 flag + u32 count (prefab/scene archives), or just u32 count
        # (.ANIM/.CLIP, which also carry a StreamInfo record); fields are identical
        for flag, nf, start in ((b[tq], _u32(b, tq + 1), tq + 5), (0, _u32(b, tq), tq + 4)):
            q, fields = start, []
            try:
                for _ in range(nf):
                    ftype = _u32(b, q)
                    fname, q = _str(b, q + 4)
                    fa, fb, fflags, fc, fd = struct.unpack_from("<iIIIi", b, q)
                    q += 20
                    fields.append(Field(ftype, fname, fa, fb, fflags, fc, fd))
            except (struct.error, IndexError):
                continue
            if q == te:
                break
        cd = ClassDef(cname, ver, flag)
        cd.fields = fields
        classes.append(cd)
        p = e
    olst = b.find(b"OLST\0", cend) - 8
    return Archive(types, classes, b, olst)


class ParseError(ValueError):
    pass


PRIM_FMT = {"Char": "b", "UChar": "B", "Short": "h", "Int": "i", "Int64": "q", "Float": "f", "Half": "e",
            "Colour3": "3f", "Vec3": "3f", "Vec4": "4f", "Colour4": "4f", "NuQuat": "4f", "Mtx": "16f",
            "NuTransform": "12f", "HalfVec3": "3e", "Colour32": "I", "Ptr": "Q", "NuHSpecial": "16s",
            "NuGuid": "16s", "ApiRenderFoliageGrid": "176s"}


class Reader:
    def __init__(self, ar: Archive):
        self.ar, self.b = ar, ar.body
        self.stats = {"mobj_ok": 0, "mobj_bad": 0}
        self._class_index = {c.name: i for i, c in enumerate(ar.classes)}
        self.handle_pre = None          # byte count before the GUID, consistent within an archive
        self.errors = []

    def read_mobj(self, o, class_idx):
        name, p, end = record(self.b, o)
        if name != "MOBJ":
            raise ParseError(f"expected MOBJ at {o:#x}, got {name!r}")
        prefix = self.b[p:p + 4]
        obj = {"_class": self.ar.classes[class_idx].name, "_prefix": prefix.hex()}
        try:
            q = self.read_fields(p + 4, class_idx, obj, end)
            if q > end:
                raise ParseError(f"{self.ar.classes[class_idx].name} MOBJ at {o:#x}: consumed {q - o} of {end - o}")
            if q < end:                            # unreflected trailing data (e.g. ApiRenderModel)
                obj["_trailing"] = self.b[q:end]
            self.stats["mobj_ok"] += 1
        except (ParseError, struct.error, IndexError) as ex:
            self.stats["mobj_bad"] += 1
            if len(self.errors) < 20:
                self.errors.append(str(ex))
            obj["_error"] = str(ex)
        return obj, end

    def read_fields(self, q, class_idx, obj, end):
        cname = self.ar.classes[class_idx].name
        if cname == "nttResourceHandle":           # custom serialization, shape varies by archive
            return self.read_resource_handle(q, obj)
        for f in self.ar.classes[class_idx].fields:
            if f.is_base:
                q = self.read_fields(q, f.type, obj, end)
                continue
            if f.c & 0x10000:                      # entity/component reference: not stored
                continue
            try:
                q, obj[f.name] = self.read_value(q, f, end)
            except (struct.error, IndexError) as ex:
                raise ParseError(f"{self.ar.classes[class_idx].name}.{f.name} (type {f.type} flags {f.flags:#x} "
                                 f"c {f.c:#x} d {f.d}) at {q:#x}: {ex}") from None
        return q

    # shapes: u32 RefType + u8 hasGuid before the GUID (prefab/scene archives), or the GUID
    # straight away (.ANIM/.CLIP). Both end with u32 length + path (1 = just the NUL = empty).
    HANDLE_PREFIXES = (5, 0)

    def read_resource_handle(self, q, obj):
        b = self.b
        order = self.HANDLE_PREFIXES if self.handle_pre is None else \
            (self.handle_pre,) + tuple(x for x in self.HANDLE_PREFIXES if x != self.handle_pre)
        for pre in order:
            p2 = q + pre
            if p2 + 20 > len(b):
                continue
            if pre == 5 and b[q + 4] not in (0, 1):
                continue
            if pre == 5 and b[q + 4] == 0:
                obj["Reference_Type"] = _u32(b, q)
                self.handle_pre = pre
                return q + 5
            n = _u32(b, p2 + 16)
            if not 0 < n <= 512 or p2 + 20 + n > len(b):
                continue
            path = b[p2 + 20:p2 + 20 + n].split(b"\0", 1)[0]
            if path and not RESOURCE_PATH.fullmatch(path):
                continue
            if pre:
                obj["Reference_Type"] = _u32(b, q)
            obj["Resource_Guid"] = b[p2:p2 + 16].hex()
            if path:
                obj["Resource_Path"] = path.decode("latin-1")
            self.handle_pre = pre
            # the guid-first shape (.ANIM/.CLIP) ends with a trailing u32
            return p2 + 20 + n + (0 if pre else 4)
        raise ParseError(f"resource handle at {q:#x}")

    def read_value(self, q, f, end):
        b = self.b
        if f.d >= 0:                               # dynamic array
            n = _u32(b, q)
            q += 4
            if n > 1_000_000:
                raise ParseError(f"array {f.name} count {n} at {q - 4:#x}")
            out = []
            for _ in range(n):
                q, v = self.read_single(q, f, end)
                out.append(v)
            return q, out
        return self.read_single(q, f, end)

    def read_single(self, q, f, end):
        b = self.b
        if f.is_class:
            return self.read_class_value(q, f.type, end)
        tname, size = self.ar.types[f.type]
        if tname == "ClassObject":
            present = b[q]
            if not present:
                return q + 1, None
            named = self._named_class(q + 1)       # .ANIM/.CLIP name the class instead of indexing it
            if named is not None:
                cls, q2 = named
                obj, q3 = self.read_mobj(q2, cls)
                return q3, obj
            cls = _u32(b, q + 1)
            obj, q2 = self.read_mobj(q + 5, cls)
            return q2, obj
        if tname in ("String", "Data"):
            n = _u32(b, q)
            raw = b[q + 4:q + 4 + n]
            return q + 4 + n, raw.split(b"\0", 1)[0].decode("latin-1") if tname == "String" else raw
        fmt = PRIM_FMT.get(tname)
        if fmt is None or size <= 0:
            raise ParseError(f"unsupported type {tname} for {f.name} at {q:#x}")
        v = struct.unpack_from("<" + fmt, b, q)
        return q + size, (v[0] if len(v) == 1 else list(v))

    def _named_class(self, q):
        """-> (class index, offset after the name) when a ClassObject is stored as a name."""
        b = self.b
        if q + 4 > len(b):
            return None
        n = _u32(b, q)
        if not 0 < n < 128 or q + 4 + n > len(b):
            return None
        name = b[q + 4:q + 4 + n].split(b"\0", 1)[0].decode("latin-1", "replace")
        idx = self._class_index.get(name)
        return None if idx is None else (idx, q + 4 + n)

    def read_class_value(self, q, class_idx, end):
        obj = {"_class": self.ar.classes[class_idx].name}
        q = self.read_fields(q, class_idx, obj, end)
        return q, obj

    def read_olst(self):
        name, p, end = record(self.b, self.ar.olst)
        n = _u32(self.b, p)
        p += 4
        objs = []
        for _ in range(n):
            cls = struct.unpack_from("<H", self.b, p)[0]
            obj, p = self.read_mobj(p + 2, cls)
            objs.append(obj)
        return objs
