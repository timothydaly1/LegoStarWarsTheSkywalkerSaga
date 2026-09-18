"""Replace the pixels of a .TEXTURE (modding).

The new image is resized to the original texture's dimensions, a mip chain is rebuilt and
each level is encoded in the original pixel format. Everything before the pixel data (resource
header, RTXT header, the leading body u32) is kept byte for byte, so the file size is unchanged.

Supported: 2D textures in BC1/BC3/BC4/BC5/BC7, BGRA8 and R16. Cube maps, arrays, volumes and
BC6H (HDR) are not supported yet.
"""
import struct

import numpy as np

from . import dds, texture
from .resource import parse_resource

ENCODERS = {"BC1": "compress_bc1", "BC3": "compress_bc3", "BC4": "compress_bc4",
            "BC5": "compress_bc5", "BC7": "compress_bc7"}


def load_image(path: str) -> np.ndarray:
    """RGBA uint8 from PNG/JPEG/TGA/... or a DDS/TEXTURE file."""
    with open(path, "rb") as f:
        head = f.read(4)
    if head == b"DDS ":
        data = open(path, "rb").read()
        info = dds.parse_dds_header(data)
        return dds.decode_rgba(info.fmt, data[info.header_size:], info.width, info.height)
    if path.upper().endswith(".TEXTURE"):
        return texture.read_texture(path).to_rgba()
    from PIL import Image
    return np.array(Image.open(path).convert("RGBA"))


def _resize(rgba: np.ndarray, w: int, h: int) -> np.ndarray:
    if rgba.shape[1] == w and rgba.shape[0] == h:
        return rgba
    from PIL import Image
    return np.array(Image.fromarray(rgba, "RGBA").resize((w, h), Image.LANCZOS))


def _encode_level(fmt: dds.PixelFormat, rgba: np.ndarray) -> bytes:
    import etcpak
    h, w = rgba.shape[:2]
    if fmt.name in ENCODERS:
        pw, ph = -(-w // 4) * 4, -(-h // 4) * 4          # pad to whole blocks
        if (pw, ph) != (w, h):
            pad = np.zeros((ph, pw, 4), np.uint8)
            pad[:h, :w] = rgba
            pad[h:, :w] = rgba[h - 1:h, :, :]
            pad[:, w:] = pad[:, w - 1:w, :]
            rgba = pad
        return getattr(etcpak, ENCODERS[fmt.name])(np.ascontiguousarray(rgba).tobytes(), pw, ph)
    if fmt.name == "BGRA8":
        return np.ascontiguousarray(rgba[..., [2, 1, 0, 3]]).tobytes()
    if fmt.name == "RGBA8":
        return np.ascontiguousarray(rgba).tobytes()
    if fmt.name == "R16":
        return (rgba[..., 0].astype(np.uint16) * 257).astype("<u2").tobytes()
    raise NotImplementedError(f"encoding {fmt.name} is not supported")


def encode_mips(fmt: dds.PixelFormat, rgba: np.ndarray, w: int, h: int, mips: int) -> bytes:
    from PIL import Image
    base = _resize(rgba, w, h)
    out = bytearray()
    for level in range(mips):
        lw, lh = max(1, w >> level), max(1, h >> level)
        img = base if level == 0 else np.array(Image.fromarray(base, "RGBA").resize((lw, lh), Image.LANCZOS))
        enc = _encode_level(fmt, img)
        want = dds.level_size(fmt, lw, lh)
        if len(enc) != want:
            raise ValueError(f"mip {level}: encoded {len(enc)} bytes, expected {want}")
        out += enc
    return bytes(out)


def import_texture(original_path: str, image, out_path: str) -> dict:
    """Write `out_path`: `original_path` with its pixels replaced by `image` (path or RGBA array)."""
    raw = open(original_path, "rb").read()
    tex = texture.read_texture(original_path)
    if tex.kind != texture.KIND_2D:
        raise NotImplementedError("only 2D textures can be imported so far")
    rgba = load_image(image) if isinstance(image, str) else image
    if tex.fmt.name in ("BC4",):                               # single channel: use luminance
        grey = (rgba[..., :3].astype(np.float32) @ np.array([0.299, 0.587, 0.114])).clip(0, 255).astype(np.uint8)
        rgba = np.dstack([grey, grey, grey, rgba[..., 3]])
    pixels = encode_mips(tex.fmt, rgba, tex.width, tex.height, tex.mips)
    if len(pixels) != len(tex.data):
        raise ValueError(f"encoded {len(pixels)} bytes but the original holds {len(tex.data)}")
    new = raw[:len(raw) - len(pixels)] + pixels
    with open(out_path, "wb") as f:
        f.write(new)
    # verify: parse the result and compare the top mip with the resized input
    check = texture.read_texture(out_path).to_rgba().astype(np.float32)
    ref = _resize(rgba, tex.width, tex.height).astype(np.float32)
    chans = 1 if tex.fmt.name == "BC4" else (2 if tex.fmt.name == "BC5" else 3)
    mse = float(((check[..., :chans] - ref[..., :chans]) ** 2).mean())
    psnr = 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)
    return {"format": tex.fmt.name, "size": (tex.width, tex.height), "mips": tex.mips, "psnr": round(psnr, 1)}
