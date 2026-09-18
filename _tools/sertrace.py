#!/usr/bin/env python3
"""Trace NTT serializer functions in the game executable.

The engine's (de)serializers call small primitives with a field-name string,
e.g.  serialize_u16(stream, &obj->m_numItems, "m_numItems", 1).
This tool prints, for a function, the sequence of primitive calls with their
field names, element sizes and counts, plus version checks and branches, so a
file format can be read straight off the loader.

    sertrace.py VA [--depth N]     trace function containing VA
    sertrace.py --find STRING      list functions referencing a string
"""
import argparse
import bisect
import re
import struct
import sys

import capstone
import pefile

EXE = __file__.rsplit('/', 2)[0] + '/LEGOSTARWARSSKYWALKERSAGA_DX11.exe'
BASE = 0x140000000
data = open(EXE, 'rb').read()
pe = pefile.PE(data=data, fast_load=True)
SECTIONS = [(s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.Name.rstrip(b'\0'))
            for s in pe.sections]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True


def file_off(rva):
    for va, sz, raw, _ in SECTIONS:
        if va <= rva < va + sz:
            return raw + rva - va
    return None


def _pdata():
    va, sz, raw, _ = [s for s in SECTIONS if s[3] == b'.pdata'][0]
    out = []
    for i in range(sz // 12):
        b, e, u = struct.unpack_from('<III', data, raw + 12 * i)
        if b:
            out.append((b, e, u))
    out.sort()
    return out


PDATA = _pdata()
STARTS = [p[0] for p in PDATA]


def pdata_entry(rva):
    i = bisect.bisect_right(STARTS, rva) - 1
    if i >= 0 and PDATA[i][0] <= rva < PDATA[i][1]:
        return PDATA[i]
    return None


def is_chained(entry):
    """UNWIND_INFO flag 4 = chained: this range is a cold chunk of another function."""
    o = file_off(entry[2] & ~1)
    return o is not None and (data[o] >> 3) & 4


def cstring(va):
    o = file_off(va - BASE)
    if o is None:
        return None
    s = data[o:o + 120].split(b'\0')[0]
    if len(s) >= 2 and all(32 <= c < 127 for c in s):
        return s.decode()
    return None


def rip_target(ins):
    for op in ins.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.base == capstone.x86.X86_REG_RIP:
            return ins.address + ins.size + op.mem.disp
    return None


def insns(start_rva, end_rva):
    o = file_off(start_rva)
    return list(md.disasm(data[o:o + end_rva - start_rva], BASE + start_rva))


def leaf_body(va, limit=300):
    """Linear sweep for leaf functions without unwind data."""
    o = file_off(va - BASE)
    out = []
    if o is None:
        return out
    for ins in md.disasm(data[o:o + 4000], va):
        out.append(ins)
        if ins.mnemonic in ('ret', 'int3') or len(out) >= limit:
            break
        if ins.mnemonic == 'jmp' and ins.operands[0].type == capstone.x86.X86_OP_IMM and not (va <= ins.operands[0].imm < va + 4000):
            break
    return out


def function_body(va, exact=False):
    """Instructions of the function containing VA, including chained cold chunks."""
    entry = pdata_entry(va - BASE)
    if entry is None or (exact and entry[0] != va - BASE):
        body = leaf_body(va)
        if not body:
            raise SystemExit(f'no code at {va:#x}')
        return body, [(va - BASE, body[-1].address + body[-1].size - BASE, 0)]
    ranges, todo, seen = [], [entry], set()
    while todo:
        e = todo.pop()
        if e[0] in seen:
            continue
        seen.add(e[0])
        ranges.append(e)
        nxt = pdata_entry(e[1])
        if nxt and nxt[0] == e[1] and nxt[0] not in seen and is_chained(nxt):
            todo.append(nxt)        # fall-through into a cold chunk
        for ins in insns(e[0], e[1]):
            if ins.group(capstone.CS_GRP_JUMP) and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_IMM:
                t = pdata_entry(ins.operands[0].imm - BASE)
                if t and t[0] not in seen and t[0] != entry[0] and is_chained(t):
                    todo.append(t)
    out = []
    for e in sorted(ranges):
        out += insns(e[0], e[1])
    return sorted(out, key=lambda i: i.address), sorted(ranges)


_size_cache = {}


def primitive_size(target):
    """Guess element byte size of a serializer primitive from its read path."""
    if target in _size_cache:
        return _size_cache[target]
    size = None
    try:
        body, _ = function_body(target, exact=True)
    except SystemExit:
        return None
    if len(body) > 120:
        _size_cache[target] = None
        return None
    while body and body[-1].mnemonic == 'int3':
        body = body[:-1]
    text = '\n'.join(f'{i.mnemonic} {i.op_str}' for i in body)
    if 'mov r8d, r9d' in text and 'jmp qword ptr [r9 + 0x60]' in text:
        size = 1                    # raw bytes
    elif re.search(r'mov r8d, 4\n(.*\n){0,4}call qword ptr \[rax \+ 0x60\]\n(.*\n){0,3}bswap edx\n(.*\n){0,2}test edx, edx', text):
        size = 'ptr'
    elif 'call qword ptr [r10 + 0x60]' in text or 'call qword ptr [rax + 0x60]' in text:
        if re.search(r'lea r8d, \[r\w+\*8\]', text) or 'mov r8d, 8' in text:
            size = 8
        elif re.search(r'lea r8d, \[r\w+\*4\]', text) or re.search(r'mov r8d, 4\b', text):
            size = 4
        elif re.search(r'lea r8d, \[r(\w+) \+ r\1\]', text) or re.search(r'mov r8d, 2\b', text):
            size = 2
        elif re.search(r'mov r8d, (e?\w+)$', text, re.M) or 'mov r8d, 1' in text:
            size = 1
    elif len(body) < 12 and body[-1].mnemonic == 'jmp' and body[-1].operands[0].type == capstone.x86.X86_OP_IMM:
        size = primitive_size(body[-1].operands[0].imm)
    _size_cache[target] = size
    return size


def trace(va, depth=0, max_depth=1, seen=None):
    seen = seen if seen is not None else set()
    body, ranges = function_body(va)
    ind = '  ' * depth
    print(f'{ind}; function {BASE + ranges[0][0]:#x} ({len(body)} insns, {len(ranges)} chunks)')
    reg_str, reg_imm = {}, {}
    prev = None
    for ins in body:
        m, ops = ins.mnemonic, ins.op_str
        if m == 'lea':
            t = rip_target(ins)
            dst = ops.split(',')[0]
            if t is not None:
                reg_str[dst] = (t, cstring(t))
        elif m == 'mov' and len(ins.operands) == 2 and ins.operands[1].type == capstone.x86.X86_OP_IMM:
            reg_imm[ops.split(',')[0]] = ins.operands[1].imm
        elif m == 'lea' and re.match(r'r9d, \[r\w+ \+ (\d+|0x[0-9a-f]+)\]$', ops):
            pass
        if m == 'cmp' and re.search(r'\[r\w+ \+ 0x24\]', ops):
            print(f'{ind}{ins.address:#x}:   VERSION cmp {ops.split(", ")[1]}')
        elif m.startswith('j') and m != 'jmp':
            cond = f'   [{prev.mnemonic} {prev.op_str}]' if prev is not None and prev.mnemonic in ('cmp', 'test') else ''
            print(f'{ind}{ins.address:#x}:     {m} {ops}{cond}')
        elif m == 'jmp':
            print(f'{ind}{ins.address:#x}:     jmp {ops}')
        elif m == 'call':
            tgt = ins.operands[0].imm if ins.operands[0].type == capstone.x86.X86_OP_IMM else None
            name = reg_str.get('r8', (None, None))[1]
            dname = reg_str.get('rdx', (None, None))[1]
            size = primitive_size(tgt) if tgt else None
            cnt = reg_imm.get('r9d')
            label = f'{tgt:#x}' if tgt else ops
            if size == 'ptr':
                print(f'{ind}{ins.address:#x}: POINTER "{name}"   ({label})')
            elif size:
                print(f'{ind}{ins.address:#x}: FIELD u{size * 8}{"[" + str(cnt) + "]" if cnt not in (None, 1) else ""} "{name}"   ({label})')
            elif name or dname:
                print(f'{ind}{ins.address:#x}: CALL {label} r8="{name}" rdx="{dname}" r9={cnt}')
                if tgt and depth < max_depth and tgt not in seen and pdata_entry(tgt - BASE):
                    seen.add(tgt)
                    trace(tgt, depth + 1, max_depth, seen)
            else:
                print(f'{ind}{ins.address:#x}: call {label}')
            reg_str.clear()
            reg_imm.clear()
        elif m == 'ret':
            print(f'{ind}{ins.address:#x}:     ret')
        prev = ins


def find_string_refs(s):
    needle = s.encode() + b'\0'
    targets = []
    for va, sz, raw, name in SECTIONS:
        if name in (b'.rdata', b'.data'):
            chunk = data[raw:raw + sz]
            for mm in re.finditer(re.escape(needle), chunk):
                if mm.start() == 0 or chunk[mm.start() - 1] == 0:
                    targets.append(BASE + va + mm.start())
    text = [s for s in SECTIONS if s[3] == b'.text'][0]
    code = data[text[2]:text[2] + text[1]]
    found = set()
    for t in targets:
        # lea reg, [rip + disp32]: 48/4c 8d xx disp32
        for mm in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]', code):
            ip = BASE + text[0] + mm.start() + 7
            disp = struct.unpack_from('<i', code, mm.start() + 3)[0]
            if ip + disp == t:
                e = pdata_entry(ip - BASE)
                found.add((BASE + e[0]) if e else ip)
    return targets, sorted(found)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('va', nargs='?')
    ap.add_argument('--depth', type=int, default=0)
    ap.add_argument('--find')
    a = ap.parse_args()
    if a.find:
        t, f = find_string_refs(a.find)
        print('string at', [hex(x) for x in t])
        print('referenced from functions', [hex(x) for x in f])
    else:
        trace(int(a.va, 16), max_depth=a.depth)


def find_callers(target):
    """Functions containing a direct call/jmp rel32 to target."""
    text = [s for s in SECTIONS if s[3] == b'.text'][0]
    code = data[text[2]:text[2] + text[1]]
    out = set()
    for mm in re.finditer(rb'[\xe8\xe9]', code):
        i = mm.start()
        if i + 5 > len(code):
            break
        rel = struct.unpack_from('<i', code, i + 1)[0]
        src = BASE + text[0] + i
        if src + 5 + rel == target:
            e = pdata_entry(src - BASE)
            out.add((BASE + e[0]) if e else src)
    return sorted(out)


def vtables_for(class_mangled):
    """MSVC x64 RTTI: TypeDescriptor name -> CompleteObjectLocators -> vtables (lists of function VAs)."""
    needle = class_mangled.encode() + b'\0'
    res = []
    rdata = [s for s in SECTIONS if s[3] == b'.rdata'][0]
    dsec = [s for s in SECTIONS if s[3] == b'.data'][0]
    for va, sz, raw, name in (dsec,):
        chunk = data[raw:raw + sz]
        for mm in re.finditer(re.escape(needle), chunk):
            td_rva = va + mm.start() - 0x10
            # COL: signature(1), offset, cdOffset, pTypeDescriptor(rva), pClassHierarchy(rva), pSelf(rva)
            rchunk = data[rdata[2]:rdata[2] + rdata[1]]
            for cm in re.finditer(re.escape(struct.pack('<I', td_rva)), rchunk):
                col_off = cm.start() - 12
                if col_off < 0 or struct.unpack_from('<I', rchunk, col_off)[0] != 1:
                    continue
                col_rva = rdata[0] + col_off
                if struct.unpack_from('<I', rchunk, col_off + 20)[0] != col_rva:
                    continue
                for vm in re.finditer(re.escape(struct.pack('<Q', BASE + col_rva)), rchunk):
                    vt = vm.start() + 8
                    funcs = []
                    for k in range(64):
                        p = struct.unpack_from('<Q', rchunk, vt + 8 * k)[0]
                        if not (BASE + 0x1000 <= p < BASE + 0x1000 + [s for s in SECTIONS if s[3] == b'.text'][0][1]):
                            break
                        funcs.append(p)
                    res.append((BASE + rdata[0] + vt, struct.unpack_from('<I', rchunk, col_off + 4)[0], funcs))
    return res
