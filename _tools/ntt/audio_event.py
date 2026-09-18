"""Sound events (.AUDIO_EVENT_PC): what the game plays, and which .AUDIO_DATA it uses.

Body chunks:
    'BANK' u8 0
    'SRCS' u32 count, then per source: u8 0, GUID16, 8 bytes, u16 len + path template
           (the '$L' in a VO path is the language), flags, then source/stream GUIDs
    'EVTS' u32 count, then per event: GUID16, u8 1, u8 0, u16 len + event name
    'END '

The resource header lists the files the event depends on, including the .AUDIO_DATA it plays,
so an event gives a readable name to an otherwise anonymous sound file.
"""
import re
import struct
from dataclasses import dataclass, field

from .resource import parse_resource

NAME_RE = re.compile(rb"[ -~]{3,}")


@dataclass
class AudioEvent:
    path: str                       # this .AUDIO_EVENT_PC
    events: list = field(default_factory=list)      # event names
    sources: list = field(default_factory=list)     # source path templates ('$L' = language)
    data: list = field(default_factory=list)        # .audio_data files it depends on


def _strings(block: bytes) -> list:
    return [m.group().decode("latin-1") for m in NAME_RE.finditer(block)]


PATH_RE = re.compile(rb"[A-Za-z0-9_][A-Za-z0-9_/#\-. $]{3,200}")


def _prefixed_strings(block: bytes) -> list:
    """u16-length-prefixed path strings inside a chunk."""
    out = []
    for m in PATH_RE.finditer(block):
        s, e = m.start(), m.end()
        if s >= 2 and struct.unpack_from(">H", block, s - 2)[0] == e - s:
            out.append(m.group().decode("latin-1"))
    return out


def read_event(path: str) -> AudioEvent:
    with open(path, "rb") as f:
        raw = f.read()
    res = parse_resource(raw, path)
    out = AudioEvent(path)
    body = res.body
    i, j = body.find(b"SRCS"), body.find(b"EVTS")
    if i >= 0:
        # sources vary in layout (volume/pitch curves, random lists ...), so pick out the
        # length-prefixed path strings rather than walking every field
        out.sources = _prefixed_strings(body[i:j if j > i else len(body)])
    i = body.find(b"EVTS")
    if i >= 0:
        count = struct.unpack_from(">I", body, i + 4)[0]
        o = i + 8
        for _ in range(min(count, 256)):
            o += 16 + 1                                       # guid, flag
            if o + 2 > len(body):
                break
            n = struct.unpack_from(">H", body, o)[0]
            if n > 512 or o + 2 + n > len(body):
                break
            out.events.append(body[o + 2:o + 2 + n].decode("latin-1"))
            o += 2 + n
    out.data = [s for s in _strings(res.header) if s.lower().endswith(".audio_data")]
    return out
