"""Replace a sound (.AUDIO_DATA) with any WAV/OGG/FLAC/MP3 file (modding).

Output is always IMA ADPCM (codec 10), the layout used by 331 of the game's sound files:
    'FMT ' (19 bytes): u16 0, u16 10, u32 rate, u32 samples, u8 channels, u8 16, u16 0,
                       u16 blockSize (1020), u8 1
    'RMS ' (optional, kept if the original had one): f32 0.02, u32 n, n x f32 RMS of all
                       channels over 20 ms windows (n = floor(duration / 20 ms))
    'DATA': 'FRST' u32 0, blocks of blockSize bytes cycling through the channels, 8 padding bytes.
            Block: s16 predictor, u8 step index, u8 0, (blockSize - 4) bytes of nibbles
            (low nibble first) -> 1 + 2 * (blockSize - 4) samples.
Codec 1 (Ogg Vorbis) originals are converted too; their SEEK table is not needed for ADPCM.
"""
import struct

import numpy as np

from .audio import INDEX_ADJ, STEP, read_chunks

BLOCK_SIZE = 1020
RMS_INTERVAL = 0.02


def load_audio(path: str, rate: int = 44100, channels: int | None = None) -> np.ndarray:
    """-> int16 array (frames, channels) resampled to `rate`."""
    import soundfile as sf
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    if channels and data.shape[1] != channels:
        mono = data.mean(axis=1, keepdims=True)
        data = np.repeat(mono, channels, axis=1) if channels > 1 else mono
    if sr != rate:
        n = int(round(len(data) * rate / sr))
        x_old = np.linspace(0, 1, len(data), endpoint=False)
        x_new = np.linspace(0, 1, n, endpoint=False)
        data = np.stack([np.interp(x_new, x_old, data[:, c]) for c in range(data.shape[1])], axis=1)
    return (np.clip(data, -1, 1) * 32767).astype(np.int16)


def encode_ima_block(samples: np.ndarray, pred: int, idx: int) -> tuple:
    """Encode 1 + 2*(BLOCK_SIZE-4) mono samples -> (block bytes, pred, idx)."""
    n = 2 * (BLOCK_SIZE - 4)
    first = int(samples[0]) if len(samples) else 0
    pred = first
    header = struct.pack("<hBB", pred, idx, 0)
    nibbles = bytearray(n)
    src = samples[1:1 + n].tolist()
    src += [src[-1] if src else first] * (n - len(src))
    for k, s in enumerate(src):
        step = STEP[idx]
        diff = s - pred
        code = 0
        if diff < 0:
            code = 8
            diff = -diff
        delta = step >> 3
        if diff >= step:
            code |= 4
            diff -= step
            delta += step
        if diff >= step >> 1:
            code |= 2
            diff -= step >> 1
            delta += step >> 1
        if diff >= step >> 2:
            code |= 1
            delta += step >> 2
        pred = pred - delta if code & 8 else pred + delta
        pred = -32768 if pred < -32768 else (32767 if pred > 32767 else pred)
        idx = min(88, max(0, idx + INDEX_ADJ[code]))
        nibbles[k] = code
    packed = bytes(nibbles[i] | (nibbles[i + 1] << 4) for i in range(0, n, 2))
    return header + packed, pred, idx


def encode_ima(pcm: np.ndarray) -> bytes:
    frames, channels = pcm.shape
    per_block = 1 + 2 * (BLOCK_SIZE - 4)
    blocks = max(1, -(-frames // per_block))
    out = bytearray(b"FRST" + struct.pack("<I", 0))
    state = [(0, 0)] * channels
    for b in range(blocks):
        chunk = pcm[b * per_block:(b + 1) * per_block]
        for c in range(channels):
            data, pred, idx = encode_ima_block(chunk[:, c] if len(chunk) else np.zeros(0, np.int16), *state[c])
            state[c] = (pred, idx)
            out += data
    out += bytes(8)                    # every game file carries 8 trailing bytes after the last block
    return bytes(out)


def rms_chunk(pcm: np.ndarray, rate: int) -> bytes:
    win = int(round(RMS_INTERVAL * rate))
    n = len(pcm) // win
    seg = pcm[:n * win].astype(np.float64).reshape(n, win, -1) / 32768.0
    vals = np.sqrt((seg ** 2).mean(axis=(1, 2))).astype("<f4")
    return struct.pack("<fI", RMS_INTERVAL, n) + vals.tobytes()


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return tag + struct.pack("<I", len(payload)) + payload


def import_audio(original_path: str, source: str, out_path: str, keep_channels=True) -> dict:
    orig = read_chunks(open(original_path, "rb").read())
    ofmt = orig["FMT "]
    channels = ofmt[12] if keep_channels else None
    rate = struct.unpack_from("<I", ofmt, 4)[0]
    pcm = load_audio(source, rate, channels)
    frames, chans = pcm.shape
    fmt = struct.pack("<HHIIBBHHB", 0, 10, rate, frames, chans, 16, 0, BLOCK_SIZE, 1)
    parts = [_chunk(b"FMT ", fmt)]
    if "RMS " in orig:
        parts.append(_chunk(b"RMS ", rms_chunk(pcm, rate)))
    parts.append(_chunk(b"DATA", encode_ima(pcm)))
    with open(out_path, "wb") as f:
        f.write(b"".join(parts))
    return {"rate": rate, "channels": chans, "frames": frames, "seconds": round(frames / rate, 2),
            "original_codec": struct.unpack_from("<H", ofmt, 2)[0]}
