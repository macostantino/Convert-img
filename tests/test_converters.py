import io
import sys
from pathlib import Path

import numpy as np
import pillow_heif
import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import converters as cv  # noqa: E402
import licensing as lic  # noqa: E402

pillow_heif.register_heif_opener()


def png_bytes(arr, mode="RGB", **kw):
    b = io.BytesIO()
    Image.fromarray(arr, mode).save(b, "PNG", **kw)
    return b.getvalue()


def tiff_cmyk(data):
    im = Image.open(io.BytesIO(data))
    assert im.mode == "CMYK"
    return im, np.asarray(im)


# ------------------------------------------------------------- PNG -> CMYK
def test_primary_colors():
    px = np.array([[[0, 0, 0], [255, 255, 255], [255, 0, 0], [0, 0, 255]]], dtype=np.uint8)
    _, c = tiff_cmyk(cv.png_to_cmyk_tiff(png_bytes(px)))
    assert tuple(c[0, 0]) == (0, 0, 0, 255)        # negro -> solo K
    assert tuple(c[0, 1]) == (0, 0, 0, 0)          # blanco -> sin tinta
    assert tuple(c[0, 2]) == (0, 255, 255, 0)      # rojo -> M + Y
    assert tuple(c[0, 3]) == (255, 255, 0, 0)      # azul -> C + M


def test_roundtrip_is_accurate():
    rng = np.random.default_rng(1)
    px = rng.integers(0, 256, (40, 60, 3), dtype=np.uint8)
    _, c = tiff_cmyk(cv.png_to_cmyk_tiff(png_bytes(px)))
    back = 255 * (1 - c[..., :3] / 255) * (1 - c[..., 3:] / 255)
    assert np.abs(back - px).max() <= 1.5


def test_alpha_is_flattened_on_white():
    px = np.zeros((2, 2, 4), dtype=np.uint8)
    px[..., 3] = [[0, 255], [0, 255]]              # columna 0 transparente, columna 1 opaca negra
    _, c = tiff_cmyk(cv.png_to_cmyk_tiff(png_bytes(px, "RGBA")))
    assert tuple(c[0, 0]) == (0, 0, 0, 0)          # transparente -> blanco
    assert tuple(c[0, 1]) == (0, 0, 0, 255)


def test_dpi_preserved_and_default():
    px = np.zeros((4, 4, 3), dtype=np.uint8)
    im, _ = tiff_cmyk(cv.png_to_cmyk_tiff(png_bytes(px, dpi=(150, 150))))
    assert tuple(round(v) for v in im.info["dpi"]) == (150, 150)
    im, _ = tiff_cmyk(cv.png_to_cmyk_tiff(png_bytes(px)))
    assert tuple(round(v) for v in im.info["dpi"]) == (300, 300)


def test_palette_gray_and_16bit():
    rng = np.random.default_rng(2)
    rgb = rng.integers(0, 256, (20, 30, 3), dtype=np.uint8)
    b = io.BytesIO(); Image.fromarray(rgb).convert("P").save(b, "PNG")
    assert tiff_cmyk(cv.png_to_cmyk_tiff(b.getvalue()))[1].shape == (20, 30, 4)
    g16 = (rng.integers(0, 65536, (10, 10))).astype(np.uint16)
    b = io.BytesIO(); Image.fromarray(g16).save(b, "PNG")
    assert tiff_cmyk(cv.png_to_cmyk_tiff(b.getvalue()))[1].shape == (10, 10, 4)


def test_chunking_gives_same_result():
    rng = np.random.default_rng(3)
    data = png_bytes(rng.integers(0, 256, (70, 50, 3), dtype=np.uint8))
    a = tiff_cmyk(cv.png_to_cmyk_tiff(data, chunk_rows=512))[1]
    b = tiff_cmyk(cv.png_to_cmyk_tiff(data, chunk_rows=7))[1]
    assert np.array_equal(a, b)


# ------------------------------------------------------------- HEIC -> JPG
def make_heic(size=(64, 48), exif_orientation=None):
    im = Image.fromarray(np.random.default_rng(4).integers(0, 256, (size[1], size[0], 3), dtype=np.uint8))
    kw = {}
    if exif_orientation:
        ex = Image.Exif(); ex[0x0112] = exif_orientation; ex[0x010F] = "TestCam"
        kw["exif"] = ex.tobytes()
    b = io.BytesIO(); im.save(b, "HEIF", **kw)
    return b.getvalue()


def test_heic_to_jpg_valid_and_quality_changes_size():
    heic = make_heic((200, 150))
    hi, lo = cv.heic_to_jpg(heic, 95), cv.heic_to_jpg(heic, 50)
    im = Image.open(io.BytesIO(hi))
    assert im.format == "JPEG" and im.size == (200, 150)
    assert len(lo) < len(hi)


def test_heic_keeps_exif_and_resets_orientation():
    out = cv.heic_to_jpg(make_heic(exif_orientation=6))
    ex = Image.open(io.BytesIO(out)).getexif()
    assert ex.get(0x010F) == "TestCam"
    assert ex.get(0x0112, 1) == 1


def test_invalid_data_raises():
    with pytest.raises(Exception):
        cv.convert("heic", b"not an image")
    with pytest.raises(Exception):
        cv.convert("png", b"not an image")
    with pytest.raises(ValueError):
        cv.convert("xyz", b"")


# ------------------------------------------------------------- nombres
def test_output_name_and_collisions():
    taken = set()
    assert cv.output_name("IMG_1.HEIC", "heic", taken) == "IMG_1.jpg"
    assert cv.output_name("img_1.heif", "heic", taken) == "img_1 (2).jpg"
    assert cv.output_name("a.png", "png") == "a.tif"


# ------------------------------------------------------------- límite
def test_limit_counter_memory_and_file(tmp_path):
    for store in (lic.MemoryStore({}), lic.FileStore(tmp_path / "a.json", tmp_path / "b.json")):
        assert lic.info(store, 3) == {"used": 0, "limit": 3, "remaining": 3}
        assert [lic.consume(store, 3) for _ in range(4)] == [True, True, True, False]
        assert lic.info(store, 3)["remaining"] == 0
        lic.reset(store)
        assert lic.info(store, 3)["used"] == 0


def test_file_counter_survives_tampering_of_one_copy(tmp_path):
    pa, pb = tmp_path / "a.json", tmp_path / "b.json"
    s = lic.FileStore(pa, pb)
    s.write(250)
    pa.write_text(pa.read_text().replace("250", "1"))      # edición manual: firma inválida, se ignora
    assert s.read() == 250
    pa.unlink(); pb.write_text("{}")                      # sin copias válidas -> 0 (limitación conocida)
    assert s.read() == 0
