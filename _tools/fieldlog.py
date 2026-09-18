"""Log named serializer field reads during emulation (name -> value)."""
import struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_RSP

# primitive -> (kind, element size)
PRIMS = {
    0x1400d9b90: ('u32', 4), 0x1400d9c50: ('u32', 4), 0x1400d9ba0: ('u16', 2),
    0x1400d9d00: ('u8', 1), 0x1400d9b10: ('bool', 1), 0x1400da280: ('mtx', 64),
    0x1400dafd0: ('vec3', 12), 0x1400dafe0: ('vec3', 12), 0x1400db110: ('vec4', 16), 0x1400da290: ('u16x', 2),
    0x1400da710: ('str', 0), 0x1400da880: ('str', 0),
}


class FieldLog:
    def __init__(self, emu, stream):
        self.emu, self.stream = emu, stream
        self.events = []          # (name, kind, dst, count, stream_pos_before)
        self.ret_hooks = {}
        self.values = []
        self.hooks = [emu.mu.hook_add(UC_HOOK_CODE, self._enter, begin=addr, end=addr) for addr in PRIMS]

    def _enter(self, mu, address, size, user):
        self.flush()
        kind, esz = PRIMS[address]
        name_ptr = mu.reg_read(UC_X86_REG_R8)
        try:
            name = self.emu.read_cstr(name_ptr, 200).decode('latin-1') if name_ptr else ''
        except Exception:
            name = '?'
        self.pending = (name, kind, esz, mu.reg_read(UC_X86_REG_RDX), mu.reg_read(UC_X86_REG_R9) & 0xFFFFFFFF,
                        self.stream.pos)
        ret = struct.unpack('<Q', mu.mem_read(mu.reg_read(UC_X86_REG_RSP), 8))[0]
        if ret not in self.ret_hooks:
            self.ret_hooks[ret] = mu.hook_add(UC_HOOK_CODE, lambda mu, a, sz, u: self.flush(), begin=ret, end=ret)

    pending = None

    def detach(self):
        for h in self.hooks + list(self.ret_hooks.values()):
            self.emu.mu.hook_del(h)
        self.hooks, self.ret_hooks = [], {}

    def flush(self):
        if not self.pending:
            return
        name, kind, esz, dst, count, pos = self.pending
        self.pending = None
        mu = self.emu.mu
        try:
            if kind == 'str':
                # NuString-like: first qword is char*
                ptr = struct.unpack('<Q', mu.mem_read(dst, 8))[0]
                val = self.emu.read_cstr(ptr, 512).decode('latin-1') if ptr else ''
            else:
                n = max(1, min(count, 64))
                raw = bytes(mu.mem_read(dst, esz * n))
                if kind in ('u32',):
                    val = list(struct.unpack(f'<{n}I', raw))
                elif kind in ('u16', 'u16x'):
                    val = list(struct.unpack(f'<{n}H', raw))
                elif kind in ('mtx', 'vec3', 'vec4'):
                    val = [round(x, 4) for x in struct.unpack(f'<{len(raw) // 4}f', raw)]
                else:
                    val = list(raw)
                if len(val) == 1:
                    val = val[0]
        except Exception as ex:
            val = f'<{ex}>'
        self.values.append((pos, name, kind, val))
