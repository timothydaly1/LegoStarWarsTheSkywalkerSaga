"""Subtitle cue lists (.SUB): plain text, one cue per line.

    //Subtitles
    Subtitle text "CS_E4L2HI_C3PO_WhatADesolatePlace" start_time 3.35138 end_time 5.20467

The quoted key is the audio event name (see audio_event.py), so a cue list gives the spoken
order and timing of a scene's dialogue and links each line to the sound file that plays it.
The displayed (localised) text itself is not in this extract.
"""
import re
from dataclasses import dataclass

CUE = re.compile(r'Subtitle\s+text\s+"([^"]+)"\s+start_time\s+(-?[\d.]+)\s+end_time\s+(-?[\d.]+)', re.I)


@dataclass
class Cue:
    key: str            # audio event name
    start: float
    end: float


def read_subtitles(path: str) -> list:
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        text = f.read()
    return [Cue(m.group(1), float(m.group(2)), float(m.group(3))) for m in CUE.finditer(text)]
