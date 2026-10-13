"""convert-img · núcleo de conversión (sin dependencias de Streamlit, fácil de testear).

Modos:
  heic -> HEIC/HEIF a JPG (conserva EXIF e ICC; corrige la orientación)
  png  -> PNG a CMYK (TIFF sin pérdida, 8 bits/canal, compresión Deflate)
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import PurePath

import numpy as np
from PIL import Image

import pillow_heif

pillow_heif.register_heif_opener()


@dataclass(frozen=True)
class Mode:
    key: str
    label: str            # texto del botón
    subtitle: str
    noun: str             # "HEIC" / "PNG"
    in_exts: tuple        # extensiones de entrada (sin punto, minúsculas)
    out_ext: str          # extensión de salida (con punto)
    out_label: str
    mime: str


MODES = {
    "heic": Mode("heic", "HEIC to JPG", "iPhone photos to standard JPEG", "HEIC",
                 ("heic", "heif"), ".jpg", "JPG", "image/jpeg"),
    "png": Mode("png", "PNG to CMYK", "Print-ready CMYK TIFF", "PNG",
                ("png",), ".tif", "CMYK TIFF", "image/tiff"),
}


# ---------------------------------------------------------------- HEIC -> JPG
def heic_to_jpg(data: bytes, quality: int = 92) -> bytes:
    quality = max(30, min(100, int(quality)))
    im = Image.open(io.BytesIO(data))
    im.load()
    exif = im.getexif()
    if exif.get(0x0112, 1) != 1:          # pillow-heif ya aplica la rotación: evitar rotar dos veces
        exif[0x0112] = 1
    kwargs = {"format": "JPEG", "quality": quality, "optimize": True, "subsampling": 0 if quality >= 90 else 2}
    if len(exif):
        kwargs["exif"] = exif.tobytes()
    icc = im.info.get("icc_profile")
    if icc:
        kwargs["icc_profile"] = icc
    out = io.BytesIO()
    im.convert("RGB").save(out, **kwargs)
    return out.getvalue()


# ---------------------------------------------------------------- PNG -> CMYK
def _to_8bit_rgba(im: Image.Image) -> Image.Image:
    if im.mode.startswith("I") or im.mode == "F":       # PNG de 16 bits en gris
        im = im.point(lambda v: v / 256).convert("L")
    return im.convert("RGBA")


def png_to_cmyk_tiff(data: bytes, chunk_rows: int = 512, black_pct: float = 0) -> bytes:
    """RGB -> CMYK matemático (sin perfil ICC) con reemplazo total de gris por negro:
         K = 255 - max(R,G,B);  C,M,Y = (max - canal) / max * 255
       Los píxeles con max(R,G,B) <= black_pct % de 255 se fuerzan a negro puro (C=M=Y=0, K=100%).
       Las transparencias se aplanan sobre fondo blanco. Conserva los DPI del PNG (300 si no trae)."""
    black_max = round(max(0.0, black_pct) / 100 * 255)
    src = Image.open(io.BytesIO(data))
    dpi = src.info.get("dpi") or (300, 300)
    dpi = (round(float(dpi[0])), round(float(dpi[1])))
    rgba = _to_8bit_rgba(src)
    w, h = rgba.size
    out = np.empty((h, w, 4), dtype=np.uint8)
    arr = np.asarray(rgba)
    for y0 in range(0, h, chunk_rows):                  # por bloques: no duplica la memoria de imágenes grandes
        blk = arr[y0:y0 + chunk_rows].astype(np.float32)
        a = blk[..., 3:4] / 255.0
        rgb = blk[..., :3] * a + 255.0 * (1.0 - a)
        mx = rgb.max(axis=2, keepdims=True)
        mx = np.where(mx <= black_max, 0.0, mx)         # casi negro -> negro puro (solo tinta K)
        safe = np.where(mx > 0, mx, 1.0)
        cmy = np.where(mx > 0, (mx - rgb) / safe * 255.0, 0.0)
        out[y0:y0 + chunk_rows, :, :3] = np.rint(cmy).astype(np.uint8)
        out[y0:y0 + chunk_rows, :, 3:] = np.rint(255.0 - mx).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(out, "CMYK").save(buf, format="TIFF", compression="tiff_adobe_deflate", dpi=dpi)
    return buf.getvalue()


# ---------------------------------------------------------------- API común
def convert(mode: str, data: bytes, quality: int = 92, black_pct: float = 0) -> bytes:
    if mode == "heic":
        return heic_to_jpg(data, quality)
    if mode == "png":
        return png_to_cmyk_tiff(data, black_pct=black_pct)
    raise ValueError(f"Unknown mode: {mode}")


def accepted_types(mode: str) -> list[str]:
    return list(MODES[mode].in_exts)


def output_name(filename: str, mode: str, taken: set[str] | None = None) -> str:
    """Nombre de salida con la extensión del modo; evita choques (a.jpg, a (2).jpg, ...)."""
    stem = PurePath(filename).stem or "image"
    ext = MODES[mode].out_ext
    name, n = stem + ext, 1
    if taken is not None:
        while name.lower() in taken:
            n += 1
            name = f"{stem} ({n}){ext}"
        taken.add(name.lower())
    return name
