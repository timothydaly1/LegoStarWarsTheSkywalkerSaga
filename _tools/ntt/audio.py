""".AUDIO_DATA sound containers.

Little-endian RIFF-style chunks: 'FMT ', optional 'SEEK', optional 'RMS ', 'DATA'.

FMT (19-20 bytes):
    u16 ?, u16 codec (1 = Ogg Vorbis, 10 = IMA ADPCM), u32 sampleRate, u32 numSamples,
    u8 channels, u8 bits (16), u16 ?, u16 blockSize (ADPCM), ...

Codec 10 DATA: 'FRST' + u32 0, then blocks of blockSize bytes. Blocks cycle through
the channels (block i belongs to channel i % channels). Each block is a standard
IMA ADPCM mono block: s16 predictor, u8 step index, u8 0, then 4-bit codes
(low nibble first), giving 1 + 2 * (blockSize - 4) samples.
Codec 1 DATA: a plain Ogg Vorbis stream.
"""
import io
import struct
import wave

import numpy as np

STEP = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66,
        73, 80, 88, 97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408,
        449, 494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066,
        2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630,
        9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767]
INDEX_ADJ = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]

# Precomputed decode tables: for each (step index, nibble) -> (delta, next index)
_DELTA = np.zeros((89, 16), np.int32)
_NEXT = np.zeros((89, 16), np.int32)
for _i, _s in enumerate(STEP):
    for _n in range(16):
        d = _s >> 3
        if _n & 4:
            d += _s
        if _n & 2:
            d += _s >> 1
        if _n & 1:
            d += _s >> 2
        _DELTA[_i, _n] = -d if _n & 8 else d
        _NEXT[_i, _n] = min(88, max(0, _i + INDEX_ADJ[_n]))


def read_chunks(data: bytes) -> dict:
    out, o = {}, 0
    while o + 8 <= len(data):
        tag = data[o:o + 4]
        size, = struct.unpack_from("<I", data, o + 4)
        out[tag.decode("latin-1")] = data[o + 8:o + 8 + size]
        o += 8 + size
    return out


def decode_ima_block(block: bytes) -> np.ndarray:
    pred, idx = struct.unpack_from("<hB", block, 0)
    idx = min(idx, 88)
    raw = np.frombuffer(block, np.uint8, offset=4)
    nibbles = np.empty(raw.size * 2, np.uint8)
    nibbles[0::2] = raw & 15
    nibbles[1::2] = raw >> 4
    out = np.empty(nibbles.size + 1, np.int16)
    out[0] = pred
    delta, nxt = _DELTA, _NEXT
    for k, n in enumerate(nibbles.tolist()):
        pred += int(delta[idx, n])
        pred = -32768 if pred < -32768 else (32767 if pred > 32767 else pred)
        idx = int(nxt[idx, n])
        out[k + 1] = pred
    return out


def decode(data: bytes):
    """Returns (kind, payload, info): kind 'ogg' -> bytes, kind 'wav' -> WAV file bytes."""
    ch = read_chunks(data)
    fmt = ch["FMT "]
    codec, rate, samples = struct.unpack_from("<HII", fmt, 2)
    channels = fmt[12]
    info = {"codec": codec, "rate": rate, "samples": samples, "channels": channels}
    body = ch["DATA"]
    if codec == 1:
        return "ogg", body, info
    if codec != 10 or body[:4] != b"FRST":
        raise NotImplementedError(f"audio codec {codec}")
    block_size, = struct.unpack_from("<H", fmt, 16)
    stream = body[8:]
    per_channel = [[] for _ in range(channels)]
    for i, off in enumerate(range(0, len(stream) - block_size + 1, block_size)):
        per_channel[i % channels].append(decode_ima_block(stream[off:off + block_size]))
    pcm = [np.concatenate(p)[:samples] if p else np.zeros(0, np.int16) for p in per_channel]
    n = min(len(p) for p in pcm)
    inter = np.stack([p[:n] for p in pcm], axis=1).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(inter.tobytes())
    return "wav", buf.getvalue(), info
