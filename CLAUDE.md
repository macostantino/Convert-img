# convert-img (by nosotros)

App Streamlit para convertir imágenes: HEIC→JPG y PNG/JPG→CMYK (TIFF) para papel de diario, con tres perfiles ICC WAN-IFRA (TIC 220 por defecto, 200 y 180) en `profiles/`. UI bilingüe: español (por defecto) e inglés, con selector de bandera; los textos viven en `TEXTS` de `app.py` (agregar siempre ambos idiomas).

- `app.py`: solo interfaz. La lógica va en `converters.py` (sin importar streamlit) y el límite en `licensing.py`.
- Para agregar una conversión: nueva función en `converters.py`, entrada en `MODES` y en `convert()`, tests en `tests/`, botón se crea solo desde `MODES` (revisar `ICONS` y los textos `titles`/`leads` en `app.py`).
- Antes de terminar un cambio: `python -m pytest -q tests`.
- Streamlit >= 1.43 (usa `st.dialog`, `download_button(on_click="ignore")`, claves `st-key-*` en el CSS).
- Cada respuesta con cambios se sube sola a GitHub (hook Stop → `scripts/autopush.sh`); no hace falta hacer commit manual.
