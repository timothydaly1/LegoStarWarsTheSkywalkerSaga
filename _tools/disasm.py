#!/usr/bin/env python3
"""Disassemble the function containing an address in the game exe.

    disasm.py VA [--max N]
"""
import bisect, struct, sys
import capstone

EXE = __file__.rsplit('/', 2)[0] + '/LEGOSTARWARSSKYWALKERSAGA_DX11.exe'
BASE = 0x140000000
d = open(EXE, 'rb').read()
import pefile
pe = pefile.PE(data=d, fast_load=True)
secs = [(s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.Name.rstrip(b'\0')) for s in pe.sections]


def off(rva):
    for va, sz, raw, _ in secs:
        if va <= rva < va + sz:
            return raw + rva - va
    raise ValueError(hex(rva))


pdata = [s for s in secs if s[3] == b'.pdata'][0]
funcs = []
p = pdata[2]
for i in range(pdata[1] // 12):
    b, e, u = struct.unpack_from('<III', d, p + 12 * i)
    if b:
        funcs.append((b, e))
funcs.sort()
starts = [f[0] for f in funcs]


def func_of(rva):
    i = bisect.bisect_right(starts, rva) - 1
    return funcs[i]


def strings_at(rva):
    try:
        o = off(rva)
    except ValueError:
        return None
    s = d[o:o + 80].split(b'\0')[0]
    if len(s) >= 3 and all(32 <= c < 127 for c in s):
        return s.decode()
    return None


def disasm(va, maxn=4000, linear=0):
    rva = va - BASE
    b, e = func_of(rva)
    if linear:
        b, e = rva, rva + linear
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    md.detail = False
    code = d[off(b):off(e)]
    print(f'; function {BASE + b:#x}-{BASE + e:#x}')
    for n, ins in enumerate(md.disasm(code, BASE + b)):
        if n > maxn:
            break
        note = ''
        if 'rip +' in ins.op_str or 'rip -' in ins.op_str:
            import re
            m = re.search(r'rip ([+-]) (0x[0-9a-f]+)', ins.op_str)
            tgt = ins.address + ins.size + (int(m.group(2), 16) if m.group(1) == '+' else -int(m.group(2), 16))
            s = strings_at(tgt - BASE)
            note = f'  ; {tgt:#x}' + (f' "{s}"' if s else '')
        if ins.mnemonic in ('mov', 'cmp') and ins.op_str.split(', ')[-1].startswith('0x'):
            v = int(ins.op_str.split(', ')[-1], 16)
            if 0x20202020 <= v <= 0x7a7a7a7a and all(32 <= ((v >> (8 * k)) & 255) < 127 for k in range(4)):
                note += '  ; ' + struct.pack('<I', v).decode()
        print(f'{ins.address:#x}: {ins.mnemonic:6} {ins.op_str}{note}')


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('va')
    ap.add_argument('--linear', type=lambda x: int(x, 0), default=0, help='disassemble N bytes from VA')
    a = ap.parse_args()
    disasm(int(a.va, 16), linear=a.linear)
