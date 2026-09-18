"""Materials (UMTL / NuMtlSceneBlock) decoded by running the game's own loader.

NuMtl is a ~3000-instruction, heavily versioned serializer, so instead of
re-implementing it we emulate NuMtlSceneBlock::Serialize (0x14023ab90) with
unicorn (see _tools/emu.py) and log every named field it reads.

Texture slots (m_Diffuse[i], m_Normal[i], m_Specular[i], m_Layer4Mask ...) are
indices ("tids") into the model's texture table: the entries of the matching
.NXG_TEXTURES file in file order (external .TEX texture pages included).
"""
import os
import sys
from dataclasses import dataclass, field

_TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)

NUMTL_SERIALIZE = 0x1402306e0
NUMTL_SCENEBLOCK = 0x14023ab90
TOPLEVEL_RETURN = 0x14023ad76      # return address of the block loop's NuMtl::Serialize call
NO_TID = 0xFFFFFFFF

_emu = None


def _get_emu():
    global _emu
    if _emu is None:
        import emu as E
        _emu = E.Emu()
    return _emu


@dataclass
class Material:
    index: int
    name: str = ""
    fields: dict = field(default_factory=dict)

    def tid(self, key):
        v = self.fields.get(key, NO_TID)
        return None if v in (NO_TID, None) or not isinstance(v, int) else v

    @property
    def diffuse(self):
        return [self.tid(f"m_Diffuse[{i}]") for i in range(4)]

    @property
    def normal(self):
        return [self.tid(f"m_Normal[{i}]") for i in range(4)]

    @property
    def specular(self):
        return [self.tid(f"m_Specular[{i}]") for i in range(4)]

    @property
    def is_shadow_only(self):
        return bool(self.fields.get("ShadowImpostor")) or bool(self.fields.get("m_DepthOnly"))

    @property
    def blend_mode(self):
        return self.fields.get("m_BlendMode", 0)

    @property
    def alpha_test(self):
        return self.fields.get("m_AlphaTest", 0)


def read_materials(body: bytes) -> list:
    """Return Material objects in material-index order for a model body (NU20 data).

    Index order: top-level materials in file order, then their nested ':VARIANT'
    materials in the order they are serialized (verified against shadow-imposter
    geometry, which always references the ShadowImpostor material index).
    """
    import struct

    import emu as E
    import fieldlog as FL
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_RSP

    start = body.find(b"LTMU")
    if start < 0:
        return []
    emu = _get_emu()
    emu.heap_ptr = E.HEAP                      # reuse the emulator between models
    stream = E.Stream(emu, body, start)
    ser = E.make_serializer(emu, stream, 0)

    top, variants = [], []
    stack = []                                 # (material, rsp at entry)
    ret_hooks = {}

    class Log(FL.FieldLog):
        def flush(self):
            before = len(self.values)
            super().flush()
            if len(self.values) > before and stack:
                _, name, _, val = self.values[-1]
                m = stack[-1][0]
                if name == "tmp" and not m.name:
                    m.name = val
                m.fields.setdefault(name, val)

    log = Log(emu, stream)

    def on_return(mu, a, sz, u):
        rsp = mu.reg_read(UC_X86_REG_RSP)
        while stack and stack[-1][1] < rsp:    # serialize frames that have returned
            log.flush()
            stack.pop()

    def on_serialize(mu, a, sz, u):
        rsp = mu.reg_read(UC_X86_REG_RSP)
        ret = struct.unpack("<Q", mu.mem_read(rsp, 8))[0]
        log.flush()
        m = Material(-1)
        (top if ret == TOPLEVEL_RETURN else variants).append(m)
        stack.append((m, rsp))
        if ret not in ret_hooks:
            ret_hooks[ret] = mu.hook_add(UC_HOOK_CODE, on_return, begin=ret, end=ret)

    hook = emu.mu.hook_add(UC_HOOK_CODE, on_serialize, begin=NUMTL_SERIALIZE, end=NUMTL_SERIALIZE)
    try:
        emu.call(NUMTL_SCENEBLOCK, [emu.alloc(0x200), ser])
    finally:
        log.flush()
        emu.mu.hook_del(hook)
        for h in ret_hooks.values():
            emu.mu.hook_del(h)
        log.detach()
    mats = top + variants
    for i, m in enumerate(mats):
        m.index = i
    return mats
