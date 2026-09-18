#!/usr/bin/env python3
"""Build a resource GUID -> file index (all NTT resources carry a GUID in their header)."""
import json
import os
import struct
import sys
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_export", "guid_index.json")


def guid_of(path):
    try:
        with open(path, "rb") as f:
            head = f.read(512)
        if head[4:8] != b".CC4" or head[8:12] != b"HSER":
            return None
        n = struct.unpack_from(">H", head, 20)[0]
        g = head[22 + n:22 + n + 16]
        return (g.hex(), os.path.relpath(path, ROOT)) if len(g) == 16 else None
    except OSError:
        return None


def build():
    files = []
    for d, dirs, fs in os.walk(ROOT):
        dirs[:] = [x for x in dirs if not x.startswith("_")]
        files += [os.path.join(d, f) for f in fs if not f.startswith(".")]
    index = {}
    with ProcessPoolExecutor() as pool:
        for r in pool.map(guid_of, files, chunksize=256):
            if r:
                index.setdefault(r[0], r[1])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(index, f)
    return index


def load():
    if not os.path.exists(OUT):
        return build()
    with open(OUT) as f:
        return json.load(f)


if __name__ == "__main__":
    idx = build()
    print(len(idx), "guids")
