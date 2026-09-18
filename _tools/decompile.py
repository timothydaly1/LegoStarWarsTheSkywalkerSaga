#!/usr/bin/env python3
"""Decompile functions of the game exe to pseudo-C with angr.

    decompile.py VA [VA ...]
Only the requested functions (and their cold chunks) are analysed, so it stays fast.
"""
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
logging.getLogger('angr').setLevel(logging.ERROR)
logging.getLogger('cle').setLevel(logging.ERROR)
logging.getLogger('pyvex').setLevel(logging.ERROR)

import angr  # noqa: E402
import sertrace as S  # noqa: E402

proj = angr.Project(S.EXE, auto_load_libs=False, load_options={'main_opts': {'base_addr': S.BASE}})


def decompile(va):
    _, ranges = S.function_body(va)
    start = S.BASE + ranges[0][0]
    regions = [(S.BASE + b, S.BASE + e) for b, e, _ in ranges]
    cfg = proj.analyses.CFGFast(regions=regions, function_starts=[start], normalize=True,
                                force_complete_scan=False, resolve_indirect_jumps=False,
                                data_references=False, show_progressbar=False)
    func = cfg.kb.functions.get(start)
    if func is None:
        print(f'// no function at {start:#x}')
        return
    dec = proj.analyses.Decompiler(func, cfg=cfg.model)
    print(f'// ---- {start:#x}')
    print(dec.codegen.text if dec.codegen else '// decompilation failed')


if __name__ == '__main__':
    for a in sys.argv[1:]:
        decompile(int(a, 16))
