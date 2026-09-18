#!/usr/bin/env python3
"""Command-line tools for LEGO Star Wars: The Skywalker Saga (NTT engine) assets.

    tss.py info FILE...                 show resource header and chunk layout
    tss.py textures OUT [--png] [--root GAME] [--filter SUBSTR]
                                        export all textures as DDS (+PNG previews)
    tss.py models OUT [--filter SUBSTR] [--all-lods] [--breakups] [--proxies]
                                        export .GHG/.GSC models as glTF binary (.glb)
    tss.py animated MODEL.GHG OUT.glb [AN4 or folder ...]
                                        export a character with animations (default: its ANIMATION folder)
    tss.py animations OUT [--filter SUBSTR]
                                        batch: one .glb per folder of .AN4 clips, on a matching skeleton
    tss.py audio OUT [--filter SUBSTR]  decode .AUDIO_DATA to .wav / .ogg and copy plain .WAV files
tss.py audio-events OUT.json        index sound events: name -> source paths and .AUDIO_DATA
tss.py subtitles OUT.json [--events audio_events.json]
                                    dialogue cue lists: VO key, timing, and the sound it plays
tss.py character PREFAB OUT.glb [AN4 or folder ...]
                                    character with costume materials, face, hair, capes, held items;
                                    animations drive the body and face rig
tss.py characters OUT [--filter SUBSTR]
tss.py scene OUT.glb LEVEL_FOLDER|SCENE_BAKED...    level geometry and props, instanced
tss.py scenes OUT [--filter SUBSTR] [--workers N]

modding (write into a mod folder that mirrors game paths):
tss.py texture-import ORIGINAL.TEXTURE IMAGE MOD_DIR   re-encode an image in the texture's own format
tss.py model-parts MODEL                               list mesh parts to choose from
tss.py model-import ORIGINAL.GHG NEW.glb MOD_DIR --special NAME [--mesh NAME]
                                                       replace one part's geometry
tss.py audio-import ORIGINAL.AUDIO_DATA SOUND MOD_DIR  WAV/OGG/FLAC/MP3 -> IMA ADPCM
tss.py mod-install MOD_DIR / mod-uninstall MOD_DIR     copy in with backups under _backup/ / restore
tss.py --overlay MOD_DIR <command> ...                 preview a mod in any exporter without installing
"""
import argparse
import os
import re
import struct
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ntt import anim, audio, dds, gltf, model, texture  # noqa: E402
from ntt.resource import iter_chunks, read_resource  # noqa: E402

GAME_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"_tools", "_export", "_backup", "_mods", ".REDIRECT"}


def cmd_info(args):
    for path in args.files:
        res = read_resource(path)
        print(f"{path}\n  version {res.version}  source {res.source_path}\n  guid {res.guid}"
              f"  header {len(res.header)}  body {len(res.body)}")
        body = res.body
        start = body.find(b".CC4")
        for off, tag, size in iter_chunks(body, max(0, start - 4)):
            print(f"  @{off:#x} {tag} {size}")


def walk(root, exts):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        for n in sorted(files):
            if n.upper().endswith(exts):
                yield os.path.join(d, n)


def save_png(rgba, path):
    from PIL import Image
    Image.fromarray(rgba, "RGBA").save(path)


def export_texture(job):
    path, rel, out, png = job
    base = os.path.join(out, os.path.splitext(rel)[0])
    os.makedirs(os.path.dirname(base), exist_ok=True)
    written = 0
    try:
        up = path.upper()
        if up.endswith(".TEXTURE"):
            tex = texture.read_texture(path)
            with open(base + ".dds", "wb") as f:
                f.write(tex.to_dds())
            if png:
                save_png(tex.to_rgba(), base + ".png")
            written = 1
        elif up.endswith(".NXG_TEXTURES"):
            for e in texture.read_nxg_textures(path):
                if e.external:
                    continue
                stem = os.path.splitext(os.path.basename(e.name))[0]
                os.makedirs(base, exist_ok=True)
                with open(os.path.join(base, stem + ".dds"), "wb") as f:
                    f.write(e.dds)
                written += 1
                if png:
                    info = dds.parse_dds_header(e.dds)
                    if info.fmt:
                        rgba = dds.decode_rgba(info.fmt, e.dds[info.header_size:], info.width, info.height)
                        save_png(rgba, os.path.join(base, stem + ".png"))
        return written, None
    except Exception as ex:  # keep going; report at the end
        return written, f"{rel}: {ex}" + ("" if isinstance(ex, (ValueError, NotImplementedError))
                                         else "\n" + traceback.format_exc())


def cmd_textures(args):
    exts = (".TEXTURE", ".NXG_TEXTURES")
    jobs = [(p, os.path.relpath(p, args.root), args.out, args.png)
            for p in walk(args.root, exts) if not args.filter or args.filter.upper() in p.upper()]
    total, errors = 0, []
    with ProcessPoolExecutor() as pool:
        for i, (n, err) in enumerate(pool.map(export_texture, jobs, chunksize=8), 1):
            total += n
            if err:
                errors.append(err)
            if i % 500 == 0:
                print(f"  {i}/{len(jobs)} files", flush=True)
    print(f"exported {total} textures from {len(jobs)} files, {len(errors)} errors")
    for e in errors:
        print("  " + e)


def model_textures(path):
    """Texture table for a model: entries of its .NXG_TEXTURES in order, as (name, dds bytes or None).

    External entries (.TEX texture pages) are loaded from the game folder."""
    stem = os.path.splitext(path)[0]
    table = []
    nxg = stem + ".NXG_TEXTURES"
    if not os.path.exists(nxg):
        return table
    for e in texture.read_nxg_textures(nxg):
        data = e.dds
        if e.external:
            ext = os.path.join(GAME_ROOT, *e.name.strip("/").split("/"))
            candidates = [ext, ext.upper(), os.path.join(os.path.dirname(ext).upper(), os.path.basename(ext).upper())]
            for c in candidates:
                if os.path.exists(c):
                    with open(c, "rb") as f:
                        data = f.read()
                    break
        table.append((e.name, data))
    return table


def model_materials(mdl_path):
    from ntt import material
    from ntt.resource import read_resource
    try:
        return material.read_materials(read_resource(mdl_path).body)
    except Exception as ex:
        print(f"  materials failed for {mdl_path}: {ex}", flush=True)
        return []


def export_model(job):
    path, rel, out, opts = job
    try:
        mdl = model.read_model(path)
        lods = tuple(range(len(mdl.skeletons))) if opts["all_lods"] else (0,)
        glb = gltf.model_to_glb(mdl, lods=lods, breakups=opts["breakups"],
                                textures=model_textures(path), keep_proxies=opts["proxies"],
                                materials=model_materials(path))
        dst = os.path.join(out, os.path.splitext(rel)[0] + ".glb")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(glb)
        return 1, None
    except Exception as ex:
        return 0, f"{rel}: {ex}"


def cmd_models(args):
    opts = {"all_lods": args.all_lods, "breakups": args.breakups, "proxies": args.proxies}
    jobs = [(p, os.path.relpath(p, args.root), args.out, opts)
            for p in walk(args.root, (".GHG", ".GSC")) if not args.filter or args.filter.upper() in p.upper()]
    total, errors = 0, []
    with ProcessPoolExecutor() as pool:
        for i, (n, err) in enumerate(pool.map(export_model, jobs, chunksize=2), 1):
            total += n
            if err:
                errors.append(err)
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)} files", flush=True)
    print(f"exported {total} of {len(jobs)} models, {len(errors)} errors")
    for e in errors:
        print("  " + e)


def load_clips(sources, num_joints):
    files = []
    for src in sources:
        if os.path.isdir(src):
            files += list(walk(src, (".AN4",)))
        else:
            files.append(src)
    clips, skipped = [], []
    for f in files:
        with open(f, "rb") as fh:
            data = fh.read()
        name = os.path.splitext(os.path.basename(f))[0].replace("_DX11", "")
        ok = False
        for base, endian in anim.find_headers(data):
            try:
                clip = anim.decode_clip(data, base, endian)
            except (NotImplementedError, struct.error, IndexError) as ex:
                skipped.append(f"{name}: {ex}")
                break
            if clip.num_nodes == num_joints:
                clips.append((name, clip))
                ok = True
                break
        if not ok and not any(s.startswith(name + ":") for s in skipped):
            skipped.append(f"{name}: no clip with {num_joints} nodes")
    return clips, skipped


def cmd_animated(args):
    mdl = model.read_model(args.model)
    if not mdl.skeletons:
        raise SystemExit("model has no skeleton")
    sources = args.anims or [os.path.join(os.path.dirname(args.model), "ANIMATION")]
    clips, skipped = load_clips(sources, len(mdl.skeletons[0].joints))
    glb = gltf.model_to_glb(mdl, textures=model_textures(args.model), clips=clips,
                            materials=model_materials(args.model))
    with open(args.out, "wb") as f:
        f.write(glb)
    print(f"wrote {args.out}: {len(clips)} clips, {len(skipped)} skipped")
    for s in skipped:
        print("  skipped " + s)


def _skeleton_index(root):
    """Joint count of the first skeleton of every .GHG (cached per run)."""
    index = {}
    for p in walk(root, (".GHG",)):
        try:
            mdl = model.read_model(p)
        except Exception:
            continue
        if mdl.skeletons:
            index[p] = len(mdl.skeletons[0].joints)
    return index


def _pick_skeleton(folder, joints, index, root):
    here = os.path.abspath(folder)
    for _ in range(3):
        cands = [p for p, n in index.items() if n == joints and os.path.dirname(os.path.abspath(p)) == here]
        if cands:
            return sorted(cands)[0]
        here = os.path.dirname(here)
    rel = os.path.relpath(folder, root).upper()
    supers = [p for p, n in index.items() if n == joints and "SUPER_CHARACTER" in p.upper()]
    for fam in ("MINIFIG", "SMALL", "BIGFIG", "BABY", "ASTROMECH", "B1DROID", "FROG"):
        if fam in rel:
            named = [p for p in supers if fam in os.path.basename(p).upper() and "CUSTOMISER" not in p.upper()]
            if named:
                return sorted(named, key=len)[0]
    supers = [p for p in supers if "CUSTOMISER" not in p.upper() and "SKELETON" not in p.upper()]
    return sorted(supers, key=len)[0] if supers else None


def export_anim_folder(job):
    folder, model_path, out_path = job
    try:
        mdl = model.read_model(model_path)
        files = [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.upper().endswith(".AN4")]
        clips, _ = load_clips(files, len(mdl.skeletons[0].joints))
        if not clips:
            return 0, f"{folder}: no usable clips"
        glb = gltf.model_to_glb(mdl, textures=model_textures(model_path), clips=clips,
                                materials=model_materials(model_path))
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(glb)
        return len(clips), None
    except Exception as ex:
        return 0, f"{folder}: {ex}"


def cmd_animations(args):
    import collections
    folders = collections.defaultdict(list)
    for p in walk(args.root, (".AN4",)):
        if not args.filter or args.filter.upper() in p.upper():
            folders[os.path.dirname(p)].append(p)
    print(f"indexing skeletons...", flush=True)
    index = _skeleton_index(args.root)
    jobs, unmatched = [], []
    for folder, files in sorted(folders.items()):
        joints = None
        for f in files:
            with open(f, "rb") as fh:
                data = fh.read()
            hs = anim.find_headers(data)
            if hs:
                base, endian = hs[0]
                joints = struct.unpack_from(endian + "H", data, base + 4)[0]
                break
        skel = _pick_skeleton(folder, joints, index, args.root) if joints else None
        if not skel:
            unmatched.append(f"{os.path.relpath(folder, args.root)} ({joints} joints)")
            continue
        out = os.path.join(args.out, os.path.relpath(folder, args.root) + ".glb")
        jobs.append((folder, skel, out))
    total, errors = 0, []
    with ProcessPoolExecutor() as pool:
        for i, (n, err) in enumerate(pool.map(export_anim_folder, jobs), 1):
            total += n
            if err:
                errors.append(err)
            if i % 50 == 0:
                print(f"  {i}/{len(jobs)} folders", flush=True)
    print(f"exported {total} clips in {len(jobs)} folders; {len(unmatched)} folders without a skeleton, {len(errors)} errors")
    for u in unmatched:
        print("  no skeleton: " + u)
    for e in errors:
        print("  " + e)


def export_audio(job):
    path, rel, out = job
    try:
        base = os.path.join(out, os.path.splitext(rel)[0])
        os.makedirs(os.path.dirname(base), exist_ok=True)
        with open(path, "rb") as f:
            data = f.read()
        if path.upper().endswith(".WAV"):
            twin = os.path.splitext(path)[0] + ".AUDIO_DATA"
            suffix = "_wav" if os.path.exists(twin) else ""       # avoid clobbering the decoded twin
            with open(base + suffix + ".wav", "wb") as f:
                f.write(data)
            return 1, None
        kind, payload, _ = audio.decode(data)
        with open(base + "." + kind, "wb") as f:
            f.write(payload)
        return 1, None
    except Exception as ex:
        return 0, f"{rel}: {ex}"


def cmd_audio(args):
    jobs = [(p, os.path.relpath(p, args.root), args.out)
            for p in walk(args.root, (".AUDIO_DATA", ".WAV")) if not args.filter or args.filter.upper() in p.upper()]
    total, errors = 0, []
    with ProcessPoolExecutor() as pool:
        for i, (n, err) in enumerate(pool.map(export_audio, jobs, chunksize=4), 1):
            total += n
            if err:
                errors.append(err)
            if i % 200 == 0:
                print(f"  {i}/{len(jobs)} files", flush=True)
    print(f"exported {total} of {len(jobs)} sounds, {len(errors)} errors")
    for e in errors:
        print("  " + e)


def cmd_character(args):
    from ntt import character
    clips = []
    files = []
    for src in args.anims:
        files += list(walk(src, (".AN4",))) if os.path.isdir(src) else [src]
    for f in files:
        tracks = character.load_an4_tracks(f)
        if tracks:
            clips.append((os.path.splitext(os.path.basename(f))[0].replace("_DX11", ""), tracks,
                          character.clip_roles(f)))
    if files:
        print(f"{len(clips)} animations from {len(files)} files")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(character.character_to_glb(args.prefab, clips))
    print(f"wrote {args.out}")


CHARACTER_SKIP = ("SUPER_CHARACTER", "TEMPLATECHARACTERS", "ITEM", "WEAPONS", "LEVELANIMS", "SHAREDANIMS")


def export_character(job):
    prefab, out_path = job
    from ntt import character
    try:
        glb = character.character_to_glb(prefab)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(glb)
        return None
    except Exception as ex:
        return f"{prefab}: {type(ex).__name__}: {ex}"


def cmd_characters(args):
    chars = os.path.join(args.root, "CHARS")
    jobs = []
    for p in walk(chars, (".PREFAB_BAKED",)):
        rel = os.path.relpath(p, chars)
        if any(k in rel.upper().split(os.sep)[0] for k in CHARACTER_SKIP):
            continue
        if args.filter and args.filter.upper() not in rel.upper():
            continue
        jobs.append((p, os.path.join(args.out, os.path.splitext(rel)[0] + ".glb")))
    errors = []
    with ProcessPoolExecutor() as pool:
        for i, err in enumerate(pool.map(export_character, jobs, chunksize=4), 1):
            if err:
                errors.append(err)
            if i % 100 == 0:
                print(f"  {i}/{len(jobs)}", flush=True)
    print(f"exported {len(jobs) - len(errors)}/{len(jobs)} characters")
    for e in errors:
        print("  " + e)


def cmd_scene(args):
    import glob
    from ntt import scene
    paths = []
    for a in args.scenes:
        if os.path.isdir(a):
            paths += sorted(glob.glob(os.path.join(a, "*.SCENE_BAKED")))
        else:
            paths.append(a)
    glb, stats = scene.scene_to_glb(paths, args.filter)
    with open(args.out, "wb") as f:
        f.write(glb)
    print(f"wrote {args.out} ({len(glb) / 1e6:.1f} MB): " +
          ", ".join(f"{k} {v}" for k, v in stats.items() if not isinstance(v, list)))
    missing = sorted(set(stats.get("missing_paths", [])))
    if missing:
        print(f"  {len(missing)} referenced models are not in this extract, e.g. {missing[0]}")
    for e in stats.get("errors", [])[:20]:
        print("  error: " + e)


def cmd_texture_import(args):
    from ntt import texture_import
    rel = os.path.relpath(os.path.abspath(args.original), GAME_ROOT)
    if rel.startswith(".."):
        raise SystemExit("original texture must be inside the game folder")
    out = os.path.join(args.mod_dir, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    info = texture_import.import_texture(args.original, args.image, out)
    print(f"wrote {out}: {info['format']} {info['size'][0]}x{info['size'][1]}, {info['mips']} mips, "
          f"PSNR {info['psnr']} dB")


def export_scene_folder(job):
    import glob
    from ntt import scene
    folder, out = job
    try:
        glb, stats = scene.scene_to_glb(sorted(glob.glob(os.path.join(folder, "*.SCENE_BAKED"))))
        if not stats.get("instances"):
            return folder, 0, len(set(stats.get("missing_paths", []))), None
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(glb)
        return folder, stats["instances"], len(set(stats.get("missing_paths", []))), None
    except Exception as ex:
        return folder, 0, 0, f"{type(ex).__name__}: {ex}"


def cmd_scenes(args):
    levels = os.path.join(args.root, "LEVELS")
    jobs = []
    for d, dirs, files in os.walk(levels):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        if any(f.upper().endswith(".SCENE_BAKED") for f in files):
            rel = os.path.relpath(d, levels)
            if args.filter and args.filter.upper() not in rel.upper():
                continue
            jobs.append((d, os.path.join(args.out, rel + ".glb")))
    written = 0
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for folder, inst, missing, err in pool.map(export_scene_folder, jobs):
            rel = os.path.relpath(folder, levels)
            if err:
                print(f"  {rel}: {err}", flush=True)
            elif inst:
                written += 1
                print(f"  {rel}: {inst} instances, {missing} models missing from extract", flush=True)
    print(f"wrote {written} level scenes out of {len(jobs)} folders")


def cmd_audio_import(args):
    from ntt import audio_import
    rel = os.path.relpath(os.path.abspath(args.original), GAME_ROOT)
    if rel.startswith(".."):
        raise SystemExit("original sound must be inside the game folder")
    out = os.path.join(args.mod_dir, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    info = audio_import.import_audio(args.original, args.sound, out)
    print(f"wrote {out}: IMA ADPCM {info['channels']}ch {info['rate']} Hz, {info['seconds']} s "
          f"(original codec {info['original_codec']})")


def cmd_audio_events(args):
    """Index every .AUDIO_EVENT_PC: event name -> source paths and the .AUDIO_DATA it plays."""
    import json
    from ntt import audio_event
    files = list(walk(os.path.join(args.root, "AUDIO"), (".AUDIO_EVENT_PC",)))
    events, by_data, bad = {}, {}, 0
    for p in files:
        try:
            e = audio_event.read_event(p)
        except Exception:
            bad += 1
            continue
        for name in e.events:
            events[name] = {"sources": e.sources, "data": e.data,
                            "file": os.path.relpath(p, args.root)}
            for d in e.data:
                by_data.setdefault(d.lower(), []).append(name)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({"events": events, "by_audio_data": by_data}, f, indent=0)
    print(f"wrote {args.out}: {len(events)} events from {len(files)} files "
          f"({len(by_data)} sound files named, {bad} unreadable)")


def coverage_scene(path):
    from ntt import baked, character
    counts = {}
    try:
        ar = baked.read_archive(open(path, "rb").read())
        objs = baked.Reader(ar).read_olst()
    except Exception:
        return counts

    def walk(o):
        if isinstance(o, dict):
            rp = o.get("Resource_Path")
            if rp and rp.rsplit(".", 1)[-1].lower() in ("gsc", "ghg", "model", "texture", "prefab_baked"):
                ext = rp.rsplit(".", 1)[-1].lower()
                have = character.resolve_path(rp) is not None
                c = counts.setdefault(ext, {"have": 0, "missing": 0, "examples": set()})
                c["have" if have else "missing"] += 1
                if not have and len(c["examples"]) < 3:
                    c["examples"].add(rp)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(objs)
    return counts


def cmd_coverage(args):
    """Report how many assets the levels reference that are actually present in this extract."""
    total = {}
    files = [p for p in walk(os.path.join(args.root, "LEVELS"), (".SCENE_BAKED",))]
    if args.filter:
        files = [p for p in files if args.filter.upper() in p.upper()]
    for i, p in enumerate(files, 1):
        for ext, c in coverage_scene(p).items():
            t = total.setdefault(ext, {"have": 0, "missing": 0, "examples": set()})
            t["have"] += c["have"]
            t["missing"] += c["missing"]
            if len(t["examples"]) < 3:
                t["examples"] |= c["examples"]
        if i % 200 == 0:
            print(f"  {i}/{len(files)} scenes", flush=True)
    print(f"references in {len(files)} scene files:")
    for ext, c in sorted(total.items(), key=lambda kv: -kv[1]["have"] - kv[1]["missing"]):
        n = c["have"] + c["missing"]
        print(f"  .{ext:<13} {n:>8} refs, {c['have']:>8} present ({100*c['have']/max(n,1):5.1f}%)")
        if c["missing"]:
            print(f"                  missing e.g. {sorted(c['examples'])[0]}")


def cmd_subtitles(args):
    """Dump every .SUB cue list, linked to the audio events (and sound files) they play."""
    import json
    from ntt import audio_event, subtitles
    events = {}
    if args.events:
        with open(args.events) as f:
            events = json.load(f).get("events", {})
    # cutscene dialogue is one mixed stream per scene, named after the cue file
    by_norm = {re.sub(r"[^a-z0-9]", "", k.lower()): k for k in events}
    out, cues, linked_files = {}, 0, 0
    for p in walk(args.root, (".SUB",)):
        rel = os.path.relpath(p, args.root)
        stem = re.sub(r"[^a-z0-9]", "", os.path.splitext(os.path.basename(p))[0].lower())
        scene = by_norm.get(stem) or by_norm.get("cs" + stem)
        items = []
        for c in subtitles.read_subtitles(p):
            e = events.get(c.key) or {}
            items.append({"key": c.key, "start": c.start, "end": c.end,
                          "audio": (e.get("data") or [None])[0], "source": (e.get("sources") or [None])[0]})
        if items:
            data = (events.get(scene, {}).get("data") or []) if scene else []
            out[rel] = {"event": scene, "streams": data, "cues": items}
            cues += len(items)
            linked_files += bool(scene)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=0)
    print(f"wrote {args.out}: {cues} cues in {len(out)} files"
          + (f", {linked_files} linked to a cutscene audio stream" if events else " (pass --events for sound links)"))


def _part_choices(mdl, mats):
    """[(part index, special name, material name, vertices, triangles)] for a model."""
    out = []
    for sp in mdl.specials:
        if not 0 <= sp.clip_object < len(mdl.clip_objects):
            continue
        for item in mdl.clip_objects[sp.clip_object]:
            if item.mesh >= len(mdl.parts):
                continue
            part = mdl.parts[item.mesh]
            mat = mats[item.material] if item.material < len(mats) else None
            out.append((item.mesh, sp.name, mat.name if mat else "", part.vb_used, part.ib_count // 3))
    return out


def cmd_model_parts(args):
    mdl = model.read_model(args.model)
    mats = model_materials(args.model)
    print(f"{len(mdl.parts)} parts")
    for idx, special, mat, verts, tris in _part_choices(mdl, mats):
        print(f"  part {idx:<4} {special:<28} {mat:<28} {verts:>7} verts {tris:>7} tris")


def cmd_model_import(args):
    from ntt import model_import
    rel = os.path.relpath(os.path.abspath(args.original), GAME_ROOT)
    if rel.startswith(".."):
        raise SystemExit("original model must be inside the game folder")
    part = args.part
    if part is None:
        if not args.special:
            raise SystemExit("choose the geometry with --part N or --special NAME (see 'model-parts')")
        mdl = model.read_model(args.original)
        mats = model_materials(args.original)
        hits = [c for c in _part_choices(mdl, mats) if c[1].lower() == args.special.lower()]
        hits = [c for c in hits if not (c[2] and any(w in c[2].lower() for w in ("shadow", "occluder", "zhead")))] or hits
        if len(hits) != 1:
            raise SystemExit(f"--special {args.special!r} matches {len(hits)} parts: "
                             + ", ".join(f"part {h[0]} ({h[2]})" for h in hits) + "; use --part")
        part = hits[0][0]
    mesh = model_import.load_mesh(args.mesh_file, args.mesh)
    out = os.path.join(args.mod_dir, rel)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    info = model_import.replace_part(args.original, part, mesh, out)
    print(f"wrote {out}: part {info['part']} now {info['vertices']} verts / {info['triangles']} tris "
          f"(was {info['was'][0]} / {info['was'][1]}), {info['how']}, {info['size_delta']:+d} bytes")


BACKUP_DIR = "_backup"


def _mod_files(mod_dir):
    for d, _, files in os.walk(mod_dir):
        for f in files:
            if not f.startswith("."):
                p = os.path.join(d, f)
                yield p, os.path.relpath(p, mod_dir)


def cmd_mod_install(args):
    import shutil
    n = 0
    for src, rel in _mod_files(args.mod_dir):
        dst = os.path.join(GAME_ROOT, rel)
        backup = os.path.join(GAME_ROOT, BACKUP_DIR, rel)
        if os.path.exists(dst) and not os.path.exists(backup):
            os.makedirs(os.path.dirname(backup), exist_ok=True)
            shutil.copy2(dst, backup)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    print(f"installed {n} files (originals backed up under {BACKUP_DIR}/)")


def cmd_mod_uninstall(args):
    import shutil
    n = 0
    for _, rel in _mod_files(args.mod_dir):
        dst = os.path.join(GAME_ROOT, rel)
        backup = os.path.join(GAME_ROOT, BACKUP_DIR, rel)
        if os.path.exists(backup):
            shutil.copy2(backup, dst)
            os.remove(backup)
            n += 1
        else:
            print(f"  no backup for {rel}; left as is")
    print(f"restored {n} files")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(required=True)
    p = sub.add_parser("info")
    p.add_argument("files", nargs="+")
    p.set_defaults(fn=cmd_info)
    p = sub.add_parser("textures")
    p.add_argument("out")
    p.add_argument("--root", default=GAME_ROOT)
    p.add_argument("--png", action="store_true", help="also write PNG previews of the top mip")
    p.add_argument("--filter", help="only files whose path contains this")
    p.set_defaults(fn=cmd_textures)
    p = sub.add_parser("models")
    p.add_argument("out")
    p.add_argument("--root", default=GAME_ROOT)
    p.add_argument("--filter", help="only files whose path contains this")
    p.add_argument("--all-lods", action="store_true", help="export every skeleton LOD")
    p.add_argument("--breakups", action="store_true", help="include destruction/breakup pieces")
    p.add_argument("--proxies", action="store_true", help="include shadow imposters and depth-only meshes")
    p.set_defaults(fn=cmd_models)
    p = sub.add_parser("animated")
    p.add_argument("model")
    p.add_argument("out")
    p.add_argument("anims", nargs="*", help=".AN4 files or folders")
    p.set_defaults(fn=cmd_animated)
    p = sub.add_parser("animations")
    p.add_argument("out")
    p.add_argument("--root", default=GAME_ROOT)
    p.add_argument("--filter", help="only clip paths containing this")
    p.set_defaults(fn=cmd_animations)
    p = sub.add_parser("character", help="assemble one character prefab (costume, face, hair, attachments)")
    p.add_argument("prefab")
    p.add_argument("out")
    p.add_argument("anims", nargs="*", help=".AN4 files or folders")
    p.set_defaults(fn=cmd_character)
    p = sub.add_parser("characters", help="assemble every character prefab under CHARS")
    p.add_argument("out")
    p.add_argument("--root", default=GAME_ROOT)
    p.add_argument("--filter", help="only prefab paths containing this")
    p.set_defaults(fn=cmd_characters)
    p = sub.add_parser("scene", help="assemble level SCENE_BAKED layers (or a level folder) into one glTF")
    p.add_argument("out")
    p.add_argument("scenes", nargs="+", help=".SCENE_BAKED files or level folders")
    p.add_argument("--filter", help="only models whose path contains this")
    p.set_defaults(fn=cmd_scene)
    p = sub.add_parser("scenes", help="assemble every level folder under LEVELS")
    p.add_argument("out")
    p.add_argument("--root", default=GAME_ROOT)
    p.add_argument("--filter")
    p.add_argument("--workers", type=int, default=4)
    p.set_defaults(fn=cmd_scenes)
    p = sub.add_parser("texture-import", help="replace a .TEXTURE's pixels with an image, written into a mod folder")
    p.add_argument("original")
    p.add_argument("image", help="PNG/JPEG/TGA/DDS")
    p.add_argument("mod_dir")
    p.set_defaults(fn=cmd_texture_import)
    p = sub.add_parser("audio-import", help="replace an .AUDIO_DATA sound with a WAV/OGG/FLAC/MP3, into a mod folder")
    p.add_argument("original")
    p.add_argument("sound")
    p.add_argument("mod_dir")
    p.set_defaults(fn=cmd_audio_import)
    p = sub.add_parser("audio-events", help="index sound events (name -> sources and .AUDIO_DATA)")
    p.add_argument("out")
    p.add_argument("--root", default=GAME_ROOT)
    p.set_defaults(fn=cmd_audio_events)
    p = sub.add_parser("coverage", help="how much of what the levels reference is present in this extract")
    p.add_argument("--root", default=GAME_ROOT)
    p.add_argument("--filter")
    p.set_defaults(fn=cmd_coverage)
    p = sub.add_parser("subtitles", help="dump .SUB cue lists (VO keys and timings)")
    p.add_argument("out")
    p.add_argument("--root", default=GAME_ROOT)
    p.add_argument("--events", help="audio_events.json from 'audio-events', to link cues to sounds")
    p.set_defaults(fn=cmd_subtitles)
    p = sub.add_parser("model-parts", help="list a model's mesh parts (index, special, material, size)")
    p.add_argument("model")
    p.set_defaults(fn=cmd_model_parts)
    p = sub.add_parser("model-import", help="replace a model part's geometry with a mesh from a glTF/GLB")
    p.add_argument("original")
    p.add_argument("mesh_file", help="glTF or GLB file")
    p.add_argument("mod_dir")
    p.add_argument("--part", type=int, help="part index (see 'model-parts')")
    p.add_argument("--special", help="named object whose geometry to replace")
    p.add_argument("--mesh", help="mesh name inside the glTF file")
    p.set_defaults(fn=cmd_model_import)
    p = sub.add_parser("mod-install", help="copy a mod folder into the game (originals backed up)")
    p.add_argument("mod_dir")
    p.set_defaults(fn=cmd_mod_install)
    p = sub.add_parser("mod-uninstall", help="restore the originals a mod folder replaced")
    p.add_argument("mod_dir")
    p.set_defaults(fn=cmd_mod_uninstall)
    p = sub.add_parser("audio")
    p.add_argument("out")
    p.add_argument("--root", default=GAME_ROOT)
    p.add_argument("--filter", help="only files whose path contains this")
    p.set_defaults(fn=cmd_audio)
    ap.add_argument("--overlay", help="mod folder whose files take precedence (preview mods without installing)")
    args = ap.parse_args()
    if args.overlay:
        from ntt import character
        character.set_overlay(args.overlay)
    args.fn(args)


if __name__ == "__main__":
    main()
