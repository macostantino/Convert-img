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
.st-key-mode_heic button,.st-key-mode_png button{height:auto;min-height:74px;padding:14px 18px;border-radius:16px;
  justify-content:flex-start;text-align:left;white-space:normal;border:2px solid var(--bd);background:#fff;color:var(--navy);
  box-shadow:0 1px 2px rgba(15,43,70,.05),0 8px 24px -14px rgba(15,43,70,.12)}
.st-key-mode_heic button:hover,.st-key-mode_png button:hover{border-color:var(--teal);color:var(--navy)}
.st-key-mode_heic button p,.st-key-mode_png button p{font-size:.86rem;color:var(--mu);margin:0;line-height:1.35}
.st-key-mode_heic button p strong,.st-key-mode_png button p strong{font-size:1.12rem;color:var(--navy)}
.st-key-mode_heic button[kind="primary"],.st-key-mode_png button[kind="primary"]{border:2px solid transparent;
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
    extra = " · Upgrade to the PRO version" if u["remaining"] <= 0 else ""
    st.markdown(
        f'<div class="lic {cls}"><span class="tag">Free version</span><div class="t">'
        f'Conversions used: <b>{u["used"]} / {u["limit"]}</b>{extra}<div class="mt"><div style="width:{p}%"></div></div></div></div>',
        unsafe_allow_html=True,
    )


@st.dialog("Limit reached · PRO")
def pro_dialog(limit: int) -> None:
    st.markdown(
        f"You have reached the **{limit}-conversion** limit of the free version. "
        "Upgrade to the **PRO version** to keep converting with no limits."
    )
    url = get_secret("PRO_URL")
    if url:
        st.link_button("Get the PRO version", url)
    if st.button("Got it", key="dlg_ok"):
        st.rerun()


# ------------------------------------------------------------------ estado
ss = st.session_state
ss.setdefault("mode", "heic")
ss.setdefault("uploader_n", 0)
ss.setdefault("result", None)
ss.setdefault("show_pro", False)
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
c1, c2 = st.columns([1, 3], vertical_alignment="center")
c1.image(str(LOGO), width=118)
mode = cv.MODES[ss.mode]
leads = {
    "heic": "Upload your HEIC photos, press <b>Convert</b> and download the finished JPGs. Everything runs in this app session.",
    "png": "Upload your PNG images, press <b>Convert</b> and download print-ready CMYK TIFF files. Everything runs in this app session.",
}
titles = {"heic": "<span>HEIC to JPG</span> Converter", "png": "<span>PNG to CMYK</span> Converter"}
c2.markdown(f'<div class="hero"><h1>{titles[ss.mode]}</h1><p>{leads[ss.mode]}</p></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ selector de conversión
b1, b2 = st.columns(2)
for col, m in ((b1, cv.MODES["heic"]), (b2, cv.MODES["png"])):
    with col:
        st.button(f"**{m.label}**  \n{m.subtitle}", key=f"mode_{m.key}", icon=ICONS[m.key], use_container_width=True,
                  type="primary" if ss.mode == m.key else "secondary", on_click=set_mode, args=(m.key,),
                  )

# ------------------------------------------------------------------ carga y opciones
with st.container(border=True):
    st.markdown("##### 1 · Upload your files")
    files = st.file_uploader(
        f"Select or drop your {mode.noun} files",
        type=cv.accepted_types(ss.mode), accept_multiple_files=True,
        key=f"up_{ss.mode}_{ss.uploader_n}", label_visibility="collapsed",
    )
    quality, black_pct = 92, 0
    if ss.mode == "heic":
        quality = st.slider("JPG quality", 50, 100, 92, format="%d%%")
    else:
        st.markdown(
            '<div class="note">Output is a lossless <b>CMYK TIFF</b> (8 bits per channel, Deflate compression). '
            "Transparent areas are flattened on white and the PNG's DPI is kept (300 if it has none). "
            "The conversion is mathematical, without an ICC profile.</div>", unsafe_allow_html=True)
        black_pct = st.slider("Pure black threshold", 0, 15, 5, format="%d%%",
                              help="Pixels this dark (or darker) become pure black: K 100%, with no C, M or Y. "
                                   "Use 0% to disable.")

# ------------------------------------------------------------------ conversión
usage = lic.info(store)
with st.container(border=True):
    st.markdown("##### 2 · Convert")
    n = len(files)
    left = usage["remaining"]
    if left is None:                    # sin límite
        left = n
    if n and 0 < left < n:
        st.info(f"Only **{left}** of {n} files will be converted (free version limit).")
    go = st.button("Convert", key="go", disabled=(n == 0 or left <= 0), type="primary")
    if n == 0:
        st.caption(f"No {mode.noun} files uploaded yet.")
    elif left <= 0:
        st.caption("Limit reached. Upgrade to the PRO version.")
    prog_slot = st.empty()
    status_slot = st.empty()
    if ss.result is None:
        prog_slot.progress(0.0, text="Idle")
    elif not go and ss.result["mode"] == ss.mode:
        prog_slot.progress(ss.result["prog"][0], text=ss.result["prog"][1])

    if go:
        taken: set[str] = set()
        items, ok, er, limit_hit, t0 = [], 0, 0, False, time.time()
        for i, f in enumerate(files):
            if lic.info(store)["remaining"] == 0:
                limit_hit = True
                break
            eta = f" · ~{fmt_eta((time.time() - t0) / i * (n - i))} left" if i else ""
            prog_slot.progress(i / n, text=f"Converting {f.name}{eta}  ·  {round(i / n * 100)}%  ·  {i} / {n}")
            t1 = time.time()
            try:
                data = f.getvalue()
                out = cv.convert(ss.mode, data, quality, black_pct)
                lic.consume(store, usage["limit"])
                items.append({"ok": True, "src": f.name, "out_name": cv.output_name(f.name, ss.mode, taken),
                              "bytes": out, "in_size": len(data), "ms": (time.time() - t1) * 1000})
                ok += 1
            except Exception as e:  # archivo dañado, formato no soportado, etc.
                items.append({"ok": False, "src": f.name, "error": str(e) or e.__class__.__name__})
                er += 1
        secs = time.time() - t0
        prog = (len(items) / n if limit_hit else 1.0,
                ("Stopped: free version limit reached" if limit_hit else "Conversion complete!") + f" · {secs:.1f} s")
        prog_slot.progress(prog[0], text=prog[1])
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for it in items:
                if it["ok"]:
                    z.writestr(it["out_name"], it["bytes"])
        ss.result = {"mode": ss.mode, "items": items, "ok": ok, "er": er, "secs": secs, "prog": prog,
                     "zip": buf.getvalue(), "stamp": datetime.now().strftime("%Y%m%d-%H%M%S")}
        ss.show_pro = limit_hit
        usage = lic.info(store)

    render_usage(usage)

# ------------------------------------------------------------------ resultados y descarga
res = ss.result
if res and res["mode"] == ss.mode:
    with st.container(border=True):
        st.markdown("##### 3 · Download")
        st.markdown(
            f'<div class="tiles"><div class="tile ok"><span>Converted</span><b>{res["ok"]}</b></div>'
            f'<div class="tile er"><span>Errors</span><b>{res["er"]}</b></div>'
            f'<div class="tile"><span>Time</span><b>{res["secs"]:.1f} s</b></div></div>',
            unsafe_allow_html=True)
        if res["ok"]:
            st.download_button(f"Download all ({res['ok']} file{'s' if res['ok'] != 1 else ''}, .zip)",
                               data=res["zip"], file_name=f"convert-img-{res['mode']}-{res['stamp']}.zip",
                               mime="application/zip", key="dl_zip", on_click="ignore")
            st.markdown('<div class="note">Files are saved to the <b>Downloads</b> folder of the computer '
                        "where your browser is running.</div>", unsafe_allow_html=True)
        with st.container(height=min(360, 52 * max(2, len(res["items"]))), border=False):
            for i, it in enumerate(res["items"]):
                a, b = st.columns([5, 1], vertical_alignment="center")
                if it["ok"]:
                    a.markdown(f'<div class="row-res"><span class="st-ic ok">✓</span><span class="n" title="{it["src"]}">'
                               f'{it["src"]} → {it["out_name"]}</span><span class="m">{fmt_size(it["in_size"])} → '
                               f'{fmt_size(len(it["bytes"]))} · {it["ms"] / 1000:.1f} s</span></div>', unsafe_allow_html=True)
                    if i < MAX_ROWS_WITH_BUTTON:
                        b.download_button("Download", data=it["bytes"], file_name=it["out_name"],
                                          mime=cv.MODES[res["mode"]].mime, key=f"dl_{i}", on_click="ignore")
                else:
                    a.markdown(f'<div class="row-res"><span class="st-ic er">!</span><span class="n">{it["src"]}</span>'
                               f'<span class="m">{it["error"]}</span></div>', unsafe_allow_html=True)
        if st.button("Clear and start over"):
            ss.result, ss.uploader_n = None, ss.uploader_n + 1
            st.rerun()

if ss.show_pro:
    ss.show_pro = False
    pro_dialog(usage["limit"])

st.markdown(
    '<div class="foot"><span>convert-img · <strong>by nosotros</strong></span>'
    "<span>© 2026 nosotros</span></div>", unsafe_allow_html=True)
