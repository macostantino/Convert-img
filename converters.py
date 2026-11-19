"""convert-img · núcleo de conversión (sin dependencias de Streamlit, fácil de testear).

Modos:
  heic -> HEIC/HEIF a JPG (conserva EXIF e ICC; corrige la orientación)
  png220 / png200 / png180 (y jpg220 / jpg200 / jpg180) -> PNG (o JPG) a CMYK para papel de diario (TIFF sin pérdida, 8 bits/canal, compresión
      Deflate) con el perfil ICC WAN-IFRA de 220 / 200 / 180 % de tinta total (carpeta profiles/)
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path, PurePath

import numpy as np
from PIL import Image, ImageCms, ImageOps

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
    out_suffix: str = ""  # se agrega al nombre antes de la extensión (ej. "_CMYK")
    profile: str = ""     # perfil ICC CMYK (archivo en profiles/); vacío = conversión matemática


MODES = {
    "heic": Mode("heic", "HEIC to JPG", "iPhone photos to standard JPEG", "HEIC",
                 ("heic", "heif"), ".jpg", "JPG", "image/jpeg", "_JPG"),
}
# PNG y JPG a CMYK: un modo por perfil ICC WAN-IFRA (TIC = tinta total máxima)
for _fmt, _exts in (("png", ("png",)), ("jpg", ("jpg", "jpeg"))):
    for _tic in ("220", "200", "180"):
        MODES[f"{_fmt}{_tic}"] = Mode(f"{_fmt}{_tic}", f"{_fmt.upper()} to CMYK · TIC {_tic}", "WAN-IFRA newsprint",
                                      _fmt.upper(), _exts, ".tif", "CMYK TIFF", "image/tiff", "_CMYK",
                                      f"WANIFRA_NP26_TIC{_tic}.icc")
MODES["wm"] = Mode("wm", "Watermark", "Add your watermark", "image", ("png", "jpg", "jpeg", "heic", "heif"),
                   ".jpg", "JPG / PNG", "image/jpeg", "_WM")


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


PROFILES_DIR = Path(__file__).parent / "profiles"
WM_POSITIONS = ("br", "bl", "tr", "tl", "center")


@lru_cache(maxsize=8)
def _profile_bytes(name: str) -> bytes:
    return (PROFILES_DIR / name).read_bytes()


@lru_cache(maxsize=16)
def _transform(profile: str, src_icc: bytes | None):
    """RGB -> CMYK con el perfil de salida; colorimétrico relativo + compensación de punto negro."""
    dst = ImageCms.ImageCmsProfile(io.BytesIO(_profile_bytes(profile)))
    src = ImageCms.createProfile("sRGB")
    if src_icc:
        try:
            cand = ImageCms.ImageCmsProfile(io.BytesIO(src_icc))
            if cand.profile.xcolor_space.strip() == "RGB":
                src = cand
        except Exception:                               # perfil incrustado dañado: se asume sRGB
            pass
    return ImageCms.buildTransform(src, dst, "RGB", "CMYK",
                                   renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                                   flags=ImageCms.Flags.BLACKPOINTCOMPENSATION)


def png_to_cmyk_tiff(data: bytes, chunk_rows: int = 512, black_pct: float = 0, profile: str = "") -> bytes:
    """PNG / JPG -> TIFF CMYK. Los píxeles con max(R,G,B) <= black_pct % de 255 (y el negro exacto) se fuerzan a
       negro puro (C=M=Y=0, K=100%). Las transparencias se aplanan sobre fondo blanco. Conserva los DPI del PNG
       (300 si no trae).
       - profile = archivo ICC CMYK de profiles/: el resto de los colores se convierten con ese perfil
         (colorimétrico relativo + compensación de punto negro) y el perfil se incrusta en el TIFF.
       - sin profile: conversión matemática, sin ICC:
            K = 255 - max(R,G,B);  C,M,Y = (max - canal) / max * 255"""
    black_max = round(max(0.0, black_pct) / 100 * 255)
    src = Image.open(io.BytesIO(data))
    dpi = src.info.get("dpi") or (300, 300)
    dpi = (round(float(dpi[0])), round(float(dpi[1])))
    src_icc = src.info.get("icc_profile") if src.mode in ("RGB", "RGBA") else None
    src = ImageOps.exif_transpose(src)                  # fotos JPG: respetar la orientación EXIF
    rgba = _to_8bit_rgba(src)
    w, h = rgba.size
    out = np.empty((h, w, 4), dtype=np.uint8)
    arr = np.asarray(rgba)
    tr = _transform(profile, src_icc) if profile else None
    for y0 in range(0, h, chunk_rows):                  # por bloques: no duplica la memoria de imágenes grandes
        blk = arr[y0:y0 + chunk_rows].astype(np.float32)
        a = blk[..., 3:4] / 255.0
        rgb = blk[..., :3] * a + 255.0 * (1.0 - a)
        if tr is not None:
            rgb8 = np.ascontiguousarray(np.rint(rgb).astype(np.uint8))
            cm = np.asarray(ImageCms.applyTransform(Image.fromarray(rgb8, "RGB"), tr))
            black = rgb8.max(axis=2) <= black_max       # casi negro -> negro puro (solo tinta K)
            cm = np.where(black[..., None], np.array([0, 0, 0, 255], dtype=np.uint8), cm)
            out[y0:y0 + chunk_rows] = cm
            continue
        mx = rgb.max(axis=2, keepdims=True)
        mx = np.where(mx <= black_max, 0.0, mx)         # casi negro -> negro puro (solo tinta K)
        safe = np.where(mx > 0, mx, 1.0)
        cmy = np.where(mx > 0, (mx - rgb) / safe * 255.0, 0.0)
        out[y0:y0 + chunk_rows, :, :3] = np.rint(cmy).astype(np.uint8)
        out[y0:y0 + chunk_rows, :, 3:] = np.rint(255.0 - mx).astype(np.uint8)
    kw = {"icc_profile": _profile_bytes(profile)} if profile else {}
    buf = io.BytesIO()
    Image.fromarray(out, "CMYK").save(buf, format="TIFF", compression="tiff_adobe_deflate", dpi=dpi, **kw)
    return buf.getvalue()


# ---------------------------------------------------------------- Marca de agua
def _ascii(text: str) -> str:
    """El EXIF guarda texto ASCII: © -> (c) y se quitan los acentos (José -> Jose) para que ningún lector lo vea roto."""
    import unicodedata
    text = text.strip().replace("©", "(c)")
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def add_watermark(data: bytes, wm: bytes, position: str = "br", scale_pct: float = 10,
                  opacity_pct: float = 20, quality: int = 100, author: str = "", copyright: str = "") -> bytes:
    """Superpone la marca de agua (bytes de un PNG/JPG/WEBP) sobre la imagen.
       scale_pct = ancho de la marca como % del ancho de la foto; opacity_pct = 0-100.
       author / copyright: si se indican, se escriben en el EXIF (Artist 0x013B, Copyright 0x8298); el resto del EXIF
       original se conserva. Salida: PNG si la entrada es PNG; JPG en los demás casos (HEIC incluido)."""
    wm_im = Image.open(io.BytesIO(wm))
    wm_im.load()
    wm_im = wm_im.convert("RGBA")
    src = Image.open(io.BytesIO(data))
    src.load()
    is_png = src.format == "PNG"
    icc = src.info.get("icc_profile")
    exif = src.getexif()
    if exif.get(0x0112, 1) != 1:                        # la foto se rota abajo: evitar rotar dos veces
        exif[0x0112] = 1
    if _ascii(author):
        exif[0x013B] = _ascii(author)
    if _ascii(copyright):
        exif[0x8298] = _ascii(copyright)
    src = ImageOps.exif_transpose(src)
    base = src.convert("RGBA")
    w, h = base.size
    ww = max(1, round(w * max(1.0, min(100.0, scale_pct)) / 100))
    wh = max(1, round(wm_im.height * ww / wm_im.width))
    wm_im = wm_im.resize((ww, wh), Image.LANCZOS)
    alpha = wm_im.getchannel("A").point(lambda v: round(v * max(0.0, min(100.0, opacity_pct)) / 100))
    wm_im.putalpha(alpha)
    m = round(w * 0.03)
    x = {"bl": m, "tl": m, "br": w - ww - m, "tr": w - ww - m}.get(position, (w - ww) // 2)
    y = {"tl": m, "tr": m, "bl": h - wh - m, "br": h - wh - m}.get(position, (h - wh) // 2)
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.paste(wm_im, (x, y))
    out_im = Image.alpha_composite(base, layer)
    out = io.BytesIO()
    kw = {"icc_profile": icc} if icc else {}
    if len(exif):
        kw["exif"] = exif.tobytes()
    if is_png:
        out_im.save(out, "PNG", **kw)
    else:
        out_im.convert("RGB").save(out, "JPEG", quality=max(30, min(100, int(quality))), optimize=True,
                                   subsampling=0 if quality >= 90 else 2, **kw)
    return out.getvalue()


# ---------------------------------------------------------------- API común
def convert(mode: str, data: bytes, quality: int = 92, black_pct: float = 0, **wm_opts) -> bytes:
    if mode == "wm":
        return add_watermark(data, quality=quality, **wm_opts)
    if mode == "heic":
        return heic_to_jpg(data, quality)
    if mode in MODES and MODES[mode].profile:
        return png_to_cmyk_tiff(data, black_pct=black_pct, profile=MODES[mode].profile)
    raise ValueError(f"Unknown mode: {mode}")


def accepted_types(mode: str) -> list[str]:
    return list(MODES[mode].in_exts)


def output_name(filename: str, mode: str, taken: set[str] | None = None) -> str:
    """Nombre de salida con la extensión del modo; evita choques (a.jpg, a (2).jpg, ...)."""
    stem = PurePath(filename).stem or "image"
    ext = MODES[mode].out_ext
    if mode == "wm" and PurePath(filename).suffix.lower() == ".png":
        ext = ".png"
    stem += MODES[mode].out_suffix
    name, n = stem + ext, 1
    if taken is not None:
        while name.lower() in taken:
            n += 1
            name = f"{stem} ({n}){ext}"
        taken.add(name.lower())
    return name
