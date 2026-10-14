"""convert-img · by nosotros
Convertidor de imágenes en Streamlit: HEIC to JPG y PNG to CMYK.
Ejecutar:  streamlit run app.py
"""
from __future__ import annotations

import io
import os
import time
import zipfile
from datetime import datetime
from pathlib import Path

import streamlit as st

import converters as cv
import licensing as lic

ROOT = Path(__file__).parent
FAVICON = ROOT / "assets" / "favicon.png"
LOGO = ROOT / "assets" / "logo.png"
ICONS = {"heic": ":material/image:", "png": ":material/palette:"}
TICS = ("220", "200", "180")        # perfiles WAN-IFRA; el primero (220) es el recomendado
MAX_ROWS_WITH_BUTTON = 100          # filas con botón de descarga individual

st.set_page_config(page_title="convert-img · by nosotros", page_icon=str(FAVICON), layout="wide",
                   initial_sidebar_state="collapsed")

# ------------------------------------------------------------------ estilos
st.markdown(
    """
<style>
:root{--navy:#0f2b46;--teal:#1f9bb0;--green:#1e8a4c;--mu:#64748b;--bd:#e2e8f0;
      --grad:linear-gradient(135deg,#1f9bb0 0%,#1e8a4c 100%)}
.stApp{background:radial-gradient(900px 300px at 85% -60px,rgba(31,155,176,.12),transparent),
       radial-gradient(700px 260px at 0% -40px,rgba(30,138,76,.08),transparent),#f3f6f9}
header[data-testid="stHeader"]{background:transparent}
#MainMenu,footer{visibility:hidden}
.block-container{max-width:980px;padding-top:1.4rem;padding-bottom:2rem}
h1,h2,h3{color:var(--navy);letter-spacing:-.02em}
.hero h1{font-size:2.2rem;line-height:1.15;margin:.2rem 0 .3rem;padding:0}
.hero h1 span{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{color:var(--mu);margin:0 0 1.1rem;max-width:660px}
/* tarjetas */
div[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border-radius:16px;border-color:var(--bd);
  box-shadow:0 1px 2px rgba(15,43,70,.05),0 8px 24px -12px rgba(15,43,70,.12)}
/* botones de modo */
[class*="st-key-mode_"] button{height:auto;min-height:74px;padding:14px 18px;border-radius:16px;
  justify-content:flex-start;text-align:left;white-space:normal;border:2px solid var(--bd);background:#fff;color:var(--navy);
  box-shadow:0 1px 2px rgba(15,43,70,.05),0 8px 24px -14px rgba(15,43,70,.12)}
[class*="st-key-mode_"] button:hover{border-color:var(--teal);color:var(--navy)}
[class*="st-key-mode_"] button p{font-size:.86rem;color:var(--mu);margin:0;line-height:1.35}
[class*="st-key-mode_"] button p strong{font-size:1.12rem;color:var(--navy)}
[class*="st-key-mode_"] button[kind="primary"]{border:2px solid transparent;
  background:linear-gradient(#fff,#fff) padding-box,var(--grad) border-box;color:var(--navy);
  box-shadow:0 10px 26px -14px rgba(30,138,76,.55)}
/* botones primarios (acciones) */
.st-key-go button,.st-key-dl_zip button,.st-key-dlg_ok button{background:var(--grad);border:0;color:#fff;font-weight:700;
  border-radius:12px;padding:.65rem 1.4rem;box-shadow:0 8px 20px -8px rgba(30,138,76,.6)}
.st-key-go button:hover,.st-key-dl_zip button:hover,.st-key-dlg_ok button:hover{filter:brightness(1.06);color:#fff;border:0}
.st-key-go button:disabled{background:#d5dde6;color:#7b8794;box-shadow:none;opacity:1}
.st-key-go button:disabled p{color:#7b8794}
.st-key-go button p,.st-key-dl_zip button p{font-size:1.02rem}
/* uploader */
section[data-testid="stFileUploaderDropzone"]{border:2px dashed #b9c6d3;border-radius:14px;background:#fbfcfd}
section[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--teal)}
/* medidor de licencia */
.lic{display:flex;align-items:center;gap:12px;padding:12px 14px;border:1px solid var(--bd);border-radius:12px;background:#fbfcfd;font-size:.9rem;color:var(--mu)}
.lic .t{flex:1;min-width:0}.lic b{color:var(--navy)}
.lic .mt{height:6px;background:#e9eef3;border-radius:999px;overflow:hidden;margin-top:6px}
.lic .mt div{height:100%;background:var(--grad);border-radius:999px}
.lic.warn .mt div{background:#d97706}.lic.full{border-color:#fecaca;background:#fef2f2}.lic.full .mt div{background:#dc2626}
.tag{font-size:.72rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:3px 9px;border-radius:999px;background:#e8f6f8;color:#127184;white-space:nowrap}
.lic.full .tag{background:#fee2e2;color:#dc2626}
/* tiles */
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:.6rem 0 .2rem}
.tile{border:1px solid var(--bd);border-radius:12px;padding:10px 14px;background:#fbfcfd}
.tile span{display:block;font-size:.72rem;color:var(--mu);text-transform:uppercase;letter-spacing:.05em}
.tile b{font-size:1.5rem;color:var(--navy)}.tile.ok b{color:#16a34a}.tile.er b{color:#dc2626}
/* resultados */
.row-res{display:flex;align-items:center;gap:10px;font-size:.88rem;padding:.2rem 0}
.st-ic{width:20px;height:20px;border-radius:50%;display:inline-grid;place-items:center;color:#fff;font-size:.72rem;font-weight:700;flex:none}
.st-ic.ok{background:#16a34a}.st-ic.er{background:#dc2626}
.row-res .n{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--navy)}
.row-res .m{color:var(--mu);font-size:.8rem;white-space:nowrap}
.note{color:var(--mu);font-size:.84rem}
.foot{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;color:var(--mu);font-size:.82rem;
  border-top:1px solid var(--bd);margin-top:1.6rem;padding-top:.9rem}
.foot strong{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------ idiomas
LANGS = {"es": "🇪🇸 Español", "en": "🇬🇧 English"}
TEXTS = {
    "es": {
        "heic_label": "HEIC a JPG", "heic_sub": "Fotos de iPhone a JPEG estándar",
        "png_label": "PNG a CMYK", "png_sub": "TIFF CMYK para papel de diario",
        "profile": "Perfil de conversión", "tic220": "WAN-IFRA TIC 220 (recomendado)", "tic200": "WAN-IFRA TIC 200",
        "tic180": "WAN-IFRA TIC 180",
        "heic_title": "<span>HEIC a JPG</span> Convertidor", "png_title": "<span>PNG a CMYK</span> Convertidor",
        "heic_lead": "Sube tus fotos HEIC, pulsa <b>Convertir</b> y descarga los JPG terminados. Todo se ejecuta en esta sesión de la app.",
        "png_lead": "Sube tus imágenes PNG, pulsa <b>Convertir</b> y descarga archivos TIFF CMYK listos para imprimir. Todo se ejecuta en esta sesión de la app.",
        "step1": "1 · Sube tus archivos", "step2": "2 · Convierte", "step3": "3 · Descarga",
        "uploader": "Selecciona o arrastra tus archivos {noun}",
        "quality": "Calidad del JPG",
        "png_note": "La salida es un <b>TIFF CMYK</b> sin pérdida (8 bits por canal, compresión Deflate), convertido con el perfil ICC "
                    "<b>WAN-IFRA para papel de diario (ISO 12647-3), TIC {tic}%</b>, que queda incrustado en el archivo. "
                    "El negro puro sale solo con tinta K. Las zonas transparentes se aplanan sobre blanco y se conservan los DPI del PNG (300 si no trae).",
        "black": "Umbral de negro puro",
        "black_help": "Los píxeles así de oscuros (o más) pasan a negro puro: K 100%, sin C, M ni Y. Con 0% solo el negro exacto (RGB 0,0,0) pasa a negro puro.",
        "only_n": "Solo se convertirán **{left}** de {n} archivos (límite de la versión gratuita).",
        "convert": "Convertir",
        "no_files": "Aún no has subido archivos {noun}.",
        "limit_caption": "Límite alcanzado. Pásate a la versión PRO.",
        "idle": "En espera", "left": "faltan ~{eta}", "converting": "Convirtiendo {name}{eta}  ·  {pct}%  ·  {i} / {n}",
        "stopped": "Detenido: límite de la versión gratuita alcanzado", "done": "¡Conversión completa!",
        "converted": "Convertidos", "errors": "Errores", "time": "Tiempo",
        "dl_all": "Descargar todo ({n} archivo{s}, .zip)", "dl": "Descargar",
        "saved": "Los archivos se guardan en la carpeta <b>Descargas</b> del equipo donde corre tu navegador.",
        "clear": "Limpiar y empezar de nuevo",
        "free": "Versión gratuita", "used": "Conversiones usadas", "upgrade": "Pásate a la versión PRO",
        "dlg_title": "Límite alcanzado · PRO",
        "dlg_body": "Alcanzaste el límite de **{limit} conversiones** de la versión gratuita. "
                    "Pásate a la **versión PRO** para seguir convirtiendo sin límites.",
        "get_pro": "Obtener la versión PRO", "got_it": "Entendido",
    },
    "en": {
        "heic_label": "HEIC to JPG", "heic_sub": "iPhone photos to standard JPEG",
        "png_label": "PNG to CMYK", "png_sub": "CMYK TIFF for newsprint",
        "profile": "Conversion profile", "tic220": "WAN-IFRA TIC 220 (recommended)", "tic200": "WAN-IFRA TIC 200",
        "tic180": "WAN-IFRA TIC 180",
        "heic_title": "<span>HEIC to JPG</span> Converter", "png_title": "<span>PNG to CMYK</span> Converter",
        "heic_lead": "Upload your HEIC photos, press <b>Convert</b> and download the finished JPGs. Everything runs in this app session.",
        "png_lead": "Upload your PNG images, press <b>Convert</b> and download print-ready CMYK TIFF files. Everything runs in this app session.",
        "step1": "1 · Upload your files", "step2": "2 · Convert", "step3": "3 · Download",
        "uploader": "Select or drop your {noun} files",
        "quality": "JPG quality",
        "png_note": "Output is a lossless <b>CMYK TIFF</b> (8 bits per channel, Deflate compression) converted with the "
                    "<b>WAN-IFRA newsprint ICC profile (ISO 12647-3), TIC {tic}%</b>, which is embedded in the file. "
                    "Pure black uses the K ink only. Transparent areas are flattened on white and the PNG's DPI is kept (300 if it has none).",
        "black": "Pure black threshold",
        "black_help": "Pixels this dark (or darker) become pure black: K 100%, with no C, M or Y. With 0%, only exact black (RGB 0,0,0) becomes pure black.",
        "only_n": "Only **{left}** of {n} files will be converted (free version limit).",
        "convert": "Convert",
        "no_files": "No {noun} files uploaded yet.",
        "limit_caption": "Limit reached. Upgrade to the PRO version.",
        "idle": "Idle", "left": "~{eta} left", "converting": "Converting {name}{eta}  ·  {pct}%  ·  {i} / {n}",
        "stopped": "Stopped: free version limit reached", "done": "Conversion complete!",
        "converted": "Converted", "errors": "Errors", "time": "Time",
        "dl_all": "Download all ({n} file{s}, .zip)", "dl": "Download",
        "saved": "Files are saved to the <b>Downloads</b> folder of the computer where your browser is running.",
        "clear": "Clear and start over",
        "free": "Free version", "used": "Conversions used", "upgrade": "Upgrade to the PRO version",
        "dlg_title": "Limit reached · PRO",
        "dlg_body": "You have reached the **{limit}-conversion** limit of the free version. "
                    "Upgrade to the **PRO version** to keep converting with no limits.",
        "get_pro": "Get the PRO version", "got_it": "Got it",
    },
}


def t(key: str, **kw) -> str:
    txt = TEXTS[st.session_state.get("lang", "es")][key]
    return txt.format(**kw) if kw else txt


# ------------------------------------------------------------------ utilidades
def get_secret(name: str, default: str = "") -> str:
    v = os.getenv(name)
    if v:
        return v
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def get_store():
    if os.getenv("CONVERT_IMG_COUNTER", "file").lower() == "file":
        return lic.FileStore()
    return lic.MemoryStore(st.session_state)


def fmt_size(b: int) -> str:
    return f"{b / 1048576:.1f} MB" if b > 1048576 else f"{max(1, round(b / 1024))} KB"


def fmt_eta(s: float) -> str:
    s = int(round(s))
    return f"{s // 60} min {s % 60} s" if s >= 60 else f"{s} s"


def render_usage(u: dict) -> None:
    if not u["limit"]:                  # sin límite: el contador no se muestra al público
        return
    p = round(u["used"] / u["limit"] * 100)
    cls = "full" if p >= 100 else "warn" if p >= 80 else ""
    extra = f" · {t('upgrade')}" if u["remaining"] <= 0 else ""
    st.markdown(
        f'<div class="lic {cls}"><span class="tag">{t("free")}</span><div class="t">'
        f'{t("used")}: <b>{u["used"]} / {u["limit"]}</b>{extra}<div class="mt"><div style="width:{p}%"></div></div></div></div>',
        unsafe_allow_html=True,
    )


def pro_dialog(limit: int) -> None:
    st.markdown(t("dlg_body", limit=limit))
    url = get_secret("PRO_URL")
    if url:
        st.link_button(t("get_pro"), url)
    if st.button(t("got_it"), key="dlg_ok"):
        st.rerun()


# ------------------------------------------------------------------ estado
ss = st.session_state
ss.setdefault("mode", "heic")
ss.setdefault("tic", "220")
ss.setdefault("uploader_n", 0)
ss.setdefault("result", None)
ss.setdefault("show_pro", False)
ss.setdefault("lang", "es")
store = get_store()

# Admin (opcional): solo aparece si hay ADMIN_KEY en secrets / variable de entorno
ADMIN_KEY = get_secret("ADMIN_KEY")
if ADMIN_KEY:
    with st.sidebar:
        with st.expander("Admin"):
            k = st.text_input("Key", type="password", key="admin_key")
            st.metric("Files converted (total)", lic.info(store)["used"])
            if st.button("Reset counter") and k == ADMIN_KEY:
                lic.reset(store)
                st.success("Counter reset")
                st.rerun()


def set_mode(m: str) -> None:
    if ss.mode != m:
        ss.mode, ss.result, ss.uploader_n = m, None, ss.uploader_n + 1


# ------------------------------------------------------------------ cabecera
c1, c2, c3 = st.columns([1, 2.4, 1.2], vertical_alignment="center")
c1.image(str(LOGO), width=118)
with c3:
    pick = st.segmented_control("Language", list(LANGS), format_func=LANGS.get, default=ss.lang,
                                key="lang_pick", label_visibility="collapsed")
    if pick and pick != ss.lang:        # al des-seleccionar se mantiene el idioma actual
        ss.lang = pick
        st.rerun()
cmode = "heic" if ss.mode == "heic" else f"png{ss.tic}"   # modo de conversión real (el PNG depende del perfil)
mode = cv.MODES[cmode]
c2.markdown(f'<div class="hero"><h1>{t(ss.mode + "_title")}</h1><p>{t(ss.mode + "_lead")}</p></div>',
            unsafe_allow_html=True)

# ------------------------------------------------------------------ selector de conversión
for col, key in zip(st.columns(2), ("heic", "png")):
    with col:
        st.button(f"**{t(key + '_label')}**  \n{t(key + '_sub')}", key=f"mode_{key}", icon=ICONS[key], use_container_width=True,
                  type="primary" if ss.mode == key else "secondary", on_click=set_mode, args=(key,),
                  )

# ------------------------------------------------------------------ carga y opciones
with st.container(border=True):
    st.markdown(f"##### {t('step1')}")
    files = st.file_uploader(
        t("uploader", noun=mode.noun),
        type=cv.accepted_types(cmode), accept_multiple_files=True,
        key=f"up_{ss.mode}_{ss.uploader_n}", label_visibility="collapsed",
    )
    quality, black_pct = 92, 0
    if ss.mode == "heic":
        quality = st.slider(t("quality"), 50, 100, 92, format="%d%%")
    else:
        st.radio(t("profile"), TICS, key="tic", horizontal=True, format_func=lambda v: t("tic" + v))
        st.markdown(f'<div class="note">{t("png_note", tic=ss.tic)}</div>', unsafe_allow_html=True)
        black_pct = st.slider(t("black"), 0, 15, 5, format="%d%%", help=t("black_help"))

# ------------------------------------------------------------------ conversión
usage = lic.info(store)
with st.container(border=True):
    st.markdown(f"##### {t('step2')}")
    n = len(files)
    left = usage["remaining"]
    if left is None:                    # sin límite
        left = n
    if n and 0 < left < n:
        st.info(t("only_n", left=left, n=n))
    go = st.button(t("convert"), key="go", disabled=(n == 0 or left <= 0), type="primary")
    if n == 0:
        st.caption(t("no_files", noun=mode.noun))
    elif left <= 0:
        st.caption(t("limit_caption"))
    prog_slot = st.empty()
    status_slot = st.empty()
    if ss.result is None:
        prog_slot.progress(0.0, text=t("idle"))
    elif not go and ss.result["grp"] == ss.mode:
        prog_slot.progress(ss.result["prog"][0], text=ss.result["prog"][1])

    if go:
        taken: set[str] = set()
        items, ok, er, limit_hit, t0 = [], 0, 0, False, time.time()
        for i, f in enumerate(files):
            if lic.info(store)["remaining"] == 0:
                limit_hit = True
                break
            eta = f" · {t('left', eta=fmt_eta((time.time() - t0) / i * (n - i)))}" if i else ""
            prog_slot.progress(i / n, text=t("converting", name=f.name, eta=eta, pct=round(i / n * 100), i=i, n=n))
            t1 = time.time()
            try:
                data = f.getvalue()
                out = cv.convert(cmode, data, quality, black_pct)
                lic.consume(store, usage["limit"])
                items.append({"ok": True, "src": f.name, "out_name": cv.output_name(f.name, cmode, taken),
                              "bytes": out, "in_size": len(data), "ms": (time.time() - t1) * 1000})
                ok += 1
            except Exception as e:  # archivo dañado, formato no soportado, etc.
                items.append({"ok": False, "src": f.name, "error": str(e) or e.__class__.__name__})
                er += 1
        secs = time.time() - t0
        prog = (len(items) / n if limit_hit else 1.0,
                (t("stopped") if limit_hit else t("done")) + f" · {secs:.1f} s")
        prog_slot.progress(prog[0], text=prog[1])
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for it in items:
                if it["ok"]:
                    z.writestr(it["out_name"], it["bytes"])
        ss.result = {"grp": ss.mode, "mode": cmode, "items": items, "ok": ok, "er": er, "secs": secs, "prog": prog,
                     "zip": buf.getvalue(), "stamp": datetime.now().strftime("%Y%m%d-%H%M%S")}
        ss.show_pro = limit_hit
        usage = lic.info(store)

    render_usage(usage)

# ------------------------------------------------------------------ resultados y descarga
res = ss.result
if res and res["grp"] == ss.mode:
    with st.container(border=True):
        st.markdown(f"##### {t('step3')}")
        st.markdown(
            f'<div class="tiles"><div class="tile ok"><span>{t("converted")}</span><b>{res["ok"]}</b></div>'
            f'<div class="tile er"><span>{t("errors")}</span><b>{res["er"]}</b></div>'
            f'<div class="tile"><span>{t("time")}</span><b>{res["secs"]:.1f} s</b></div></div>',
            unsafe_allow_html=True)
        if res["ok"]:
            st.download_button(t("dl_all", n=res["ok"], s="s" if res["ok"] != 1 else ""),
                               data=res["zip"], file_name=f"convert-img-{res['mode']}-{res['stamp']}.zip",
                               mime="application/zip", key="dl_zip", on_click="ignore")
            st.markdown(f'<div class="note">{t("saved")}</div>', unsafe_allow_html=True)
        with st.container(height=min(360, 52 * max(2, len(res["items"]))), border=False):
            for i, it in enumerate(res["items"]):
                a, b = st.columns([5, 1], vertical_alignment="center")
                if it["ok"]:
                    a.markdown(f'<div class="row-res"><span class="st-ic ok">✓</span><span class="n" title="{it["src"]}">'
                               f'{it["src"]} → {it["out_name"]}</span><span class="m">{fmt_size(it["in_size"])} → '
                               f'{fmt_size(len(it["bytes"]))} · {it["ms"] / 1000:.1f} s</span></div>', unsafe_allow_html=True)
                    if i < MAX_ROWS_WITH_BUTTON:
                        b.download_button(t("dl"), data=it["bytes"], file_name=it["out_name"],
                                          mime=cv.MODES[res["mode"]].mime, key=f"dl_{i}", on_click="ignore")
                else:
                    a.markdown(f'<div class="row-res"><span class="st-ic er">!</span><span class="n">{it["src"]}</span>'
                               f'<span class="m">{it["error"]}</span></div>', unsafe_allow_html=True)
        if st.button(t("clear")):
            ss.result, ss.uploader_n = None, ss.uploader_n + 1
            st.rerun()

if ss.show_pro:
    ss.show_pro = False
    st.dialog(t("dlg_title"))(pro_dialog)(usage["limit"])

st.markdown(
    '<div class="foot"><span>convert-img · <strong>by nosotros</strong></span>'
    "<span>© 2026 nosotros</span></div>", unsafe_allow_html=True)
