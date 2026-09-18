#!/usr/bin/env python3
"""Run the game's own (de)serializer functions under a CPU emulator.

Maps the executable, provides a fake NuSerializer + stream backed by file bytes,
stubs imports/allocator calls, and records every stream read. This lets us use
the game's loaders as parsers for formats too complex to hand-decode.
"""
import struct
import sys
import os

from unicorn import Uc, UcError, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED, UC_PROT_ALL
from unicorn.x86_const import (UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9,
                               UC_X86_REG_RSP, UC_X86_REG_RIP, UC_X86_REG_GS_BASE, UC_X86_REG_XMM0)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pefile  # noqa: E402

EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'LEGOSTARWARSSKYWALKERSAGA_DX11.exe')
BASE = 0x140000000
STACK, STACK_SIZE = 0x7FF000000000, 0x200000
HEAP, HEAP_SIZE = 0x600000000, 0x40000000
STUBS = 0x500000000
TEB = 0x7FFE00000000
TLS_BLOCK, TLS_BLOCK_SIZE = 0x7FFD00000000, 0x200000

# allocator / debug helpers identified in the exe
ALLOC_GET = (0x1400bfd70, 0x1400bfd10, 0x1400bfcb0)
ALLOC = 0x1400bc7d0          # (allocator, size, align, flags, ...) -> ptr
FREE = 0x1400ba2d0
NOOPS = (0x1400acc00, 0x1400acc80, 0x1400bba90, 0x1400bb8c0, 0x1400d9570, 0x1400d9440, 0x1400d94d0,
         0x14017ade0)   # material registry add
LOCKS = {0x1400b95d0: 1, 0x1400b95f0: 0, 0x1400b9600: 1}   # critical section enter/leave/try
STRING_INTERN = 0x1400d9280  # NuConstStringManager::Get(mgr, const char*, flag) -> const char*


class Emu:
    def __init__(self, verbose=False):
        self.verbose = verbose
        data = open(EXE, 'rb').read()
        pe = pefile.PE(data=data)
        size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xFFF) & ~0xFFF
        mu = Uc(UC_ARCH_X86, UC_MODE_64)
        mu.mem_map(BASE, size, UC_PROT_ALL)
        mu.mem_write(BASE, data[:pe.OPTIONAL_HEADER.SizeOfHeaders])
        for s in pe.sections:
            raw = data[s.PointerToRawData:s.PointerToRawData + s.SizeOfRawData]
            mu.mem_write(BASE + s.VirtualAddress, raw[:max(0, min(len(raw), s.Misc_VirtualSize or len(raw)))])
        mu.mem_map(STACK, STACK_SIZE)
        mu.mem_map(HEAP, HEAP_SIZE)
        mu.mem_map(STUBS, 0x100000)
        mu.mem_map(TEB, 0x10000)
        mu.mem_map(TLS_BLOCK, TLS_BLOCK_SIZE)     # per-thread data (profiling counters live far in)
        mu.mem_write(STUBS, b'\xc3' * 0x100000)            # every stub address holds 'ret'
        mu.reg_write(UC_X86_REG_GS_BASE, TEB)
        tls_array = TEB + 0x1000
        mu.mem_write(TEB + 0x58, struct.pack('<Q', tls_array))
        for k in range(64):
            mu.mem_write(tls_array + 8 * k, struct.pack('<Q', TLS_BLOCK))
        self.mu = mu
        self.heap_ptr = HEAP
        self.handlers = {}
        self.stub_names = {}
        next_stub = STUBS
        # imports -> stubs returning 0
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
        for entry in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
            for imp in entry.imports:
                mu.mem_write(imp.address, struct.pack('<Q', next_stub))
                self.stub_names[next_stub] = f'{entry.dll.decode()}!{imp.name.decode() if imp.name else imp.ordinal}'
                next_stub += 1
        self.next_stub = next_stub
        fake_allocator = self.alloc(0x400)
        for a in ALLOC_GET:
            self.handlers[a] = self._h_ret(fake_allocator)
        self.handlers[ALLOC] = self._h_alloc
        self.handlers[FREE] = self._h_ret(0)
        for a in NOOPS:
            self.handlers[a] = self._h_ret(0)
        self.handlers[STRING_INTERN] = self._h_intern
        for a, v in LOCKS.items():
            self.handlers[a] = self._h_ret(v)
        self.interned = {}
        mu.hook_add(UC_HOOK_CODE, self._hook_code)
        mu.hook_add(UC_HOOK_MEM_UNMAPPED, self._hook_unmapped)
        self.fault = None

    # --- helpers -------------------------------------------------------------
    def alloc(self, size, align=16):
        self.heap_ptr = (self.heap_ptr + align - 1) & ~(align - 1)
        p = self.heap_ptr
        self.heap_ptr += max(size, 1)
        self.mu.mem_write(p, b'\0' * max(size, 1))
        return p

    def new_stub(self, name, handler):
        addr = self.next_stub
        self.next_stub += 1
        self.stub_names[addr] = name
        self.handlers[addr] = handler
        return addr

    def u64(self, a):
        return struct.unpack('<Q', self.mu.mem_read(a, 8))[0]

    def _return(self, value):
        mu = self.mu
        rsp = mu.reg_read(UC_X86_REG_RSP)
        ret = struct.unpack('<Q', mu.mem_read(rsp, 8))[0]
        mu.reg_write(UC_X86_REG_RSP, rsp + 8)
        mu.reg_write(UC_X86_REG_RAX, value)
        mu.reg_write(UC_X86_REG_RIP, ret)

    def _h_ret(self, value):
        def h(emu):
            emu._return(value)
        return h

    def _h_alloc(self, emu):
        size = self.mu.reg_read(UC_X86_REG_RDX)
        align = self.mu.reg_read(UC_X86_REG_R8) or 16
        self._return(self.alloc(min(size, 0x4000000), max(8, align)))

    def backtrace(self, depth=0x800):
        """Heuristic: return addresses on the stack that follow a call instruction."""
        rsp = self.mu.reg_read(UC_X86_REG_RSP)
        out = []
        for off in range(0, depth, 8):
            try:
                v = self.u64(rsp + off)
            except Exception:
                break
            if BASE + 0x1000 <= v < BASE + 0x38da000:
                prev = bytes(self.mu.mem_read(v - 5, 5))
                prev6 = bytes(self.mu.mem_read(v - 6, 6))
                if prev[0] == 0xE8 or prev6[:2] == b'\xff\x15' or bytes(self.mu.mem_read(v - 2, 2))[0] == 0xFF or bytes(self.mu.mem_read(v - 3, 3))[0] == 0xFF:
                    out.append(hex(v))
        return out[:12]

    def read_cstr(self, addr, limit=4096):
        out = bytearray()
        while len(out) < limit:
            c = self.mu.mem_read(addr + len(out), 1)[0]
            if c == 0:
                break
            out.append(c)
        return bytes(out)

    def _h_intern(self, emu):
        ptr = self.mu.reg_read(UC_X86_REG_RDX)
        if ptr == 0:
            self._return(0)
            return
        s = self.read_cstr(ptr)
        if s not in self.interned:
            p = self.alloc(len(s) + 1)
            self.mu.mem_write(p, s + b'\0')
            self.interned[s] = p
        self._return(self.interned[s])

    def _hook_code(self, mu, address, size, user):
        h = self.handlers.get(address)
        if h is not None:
            h(self)
        elif STUBS <= address < STUBS + 0x100000:
            if self.verbose:
                print('  stub call', self.stub_names.get(address, hex(address)))
            self._return(0)

    def _hook_unmapped(self, mu, access, address, size, value, user):
        self.fault = (access, address, mu.reg_read(UC_X86_REG_RIP))
        return False

    def call(self, func, args, max_insns=50_000_000):
        mu = self.mu
        rsp = STACK + STACK_SIZE - 0x1000
        rsp &= ~0xF
        sentinel = self.new_stub('<return>', lambda emu: emu.mu.emu_stop())
        rsp -= 0x28
        mu.mem_write(rsp, struct.pack('<Q', sentinel))
        mu.reg_write(UC_X86_REG_RSP, rsp)
        for reg, val in zip((UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9), args):
            mu.reg_write(reg, val)
        self.fault = None
        try:
            mu.emu_start(func, 0, count=max_insns)
        except UcError as e:
            rip = mu.reg_read(UC_X86_REG_RIP)
            raise RuntimeError(f'emulation error {e} at {rip:#x} fault={self.fault} backtrace={self.backtrace()}') from None
        return mu.reg_read(UC_X86_REG_RAX)


class Stream:
    """Fake NuStream: vtable with read(+0x60)/write(+0x68)/tell(+0x70)/size(+0x78)."""

    def __init__(self, emu: Emu, data: bytes, pos: int = 0):
        self.emu, self.data, self.pos = emu, data, pos
        self.reads = []
        self.obj = emu.alloc(0x100)
        vtable = emu.alloc(8 * 64)
        for k in range(64):
            stub = emu.new_stub(f'stream_vfunc_{k * 8:#x}', self._make(k * 8))
            emu.mu.mem_write(vtable + 8 * k, struct.pack('<Q', stub))
        emu.mu.mem_write(self.obj, struct.pack('<Q', vtable))

    def _make(self, off):
        def h(emu):
            mu = emu.mu
            if off == 0x60:                      # read(this, buf, len)
                buf, n = mu.reg_read(UC_X86_REG_RDX), mu.reg_read(UC_X86_REG_R8) & 0xFFFFFFFF
                chunk = self.data[self.pos:self.pos + n]
                chunk += b'\0' * (n - len(chunk))
                mu.mem_write(buf, chunk)
                self.reads.append((self.pos, n))
                self.pos += n
                emu._return(n)
            elif off == 0x70:
                emu._return(self.pos)
            elif off == 0x78:
                emu._return(len(self.data))
            else:
                if emu.verbose:
                    print(f'  stream vfunc {off:#x}')
                emu._return(0)
        return h


def make_serializer(emu: Emu, stream: Stream, version: int):
    ser = emu.alloc(0x400)
    emu.mu.mem_write(ser + 0x10, struct.pack('<Q', stream.obj))
    emu.mu.mem_write(ser + 0x18, struct.pack('<Q', emu.alloc(0x1000)))     # pointer/object id table
    emu.mu.mem_write(ser + 0x24, struct.pack('<I', version))
    emu.mu.mem_write(ser + 0x144, struct.pack('<I', 0))
    return ser
