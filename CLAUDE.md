# convert-img (Margarita IT)

App Streamlit para convertir imágenes: HEIC→JPG y PNG→CMYK (TIFF). UI y textos visibles **en inglés**.

- `app.py`: solo interfaz. La lógica va en `converters.py` (sin importar streamlit) y el límite en `licensing.py`.
- Para agregar una conversión: nueva función en `converters.py`, entrada en `MODES` y en `convert()`, tests en `tests/`, botón se crea solo desde `MODES` (revisar `ICONS` y los textos `titles`/`leads` en `app.py`).
- Antes de terminar un cambio: `python -m pytest -q tests`.
- Streamlit >= 1.43 (usa `st.dialog`, `download_button(on_click="ignore")`, claves `st-key-*` en el CSS).
- Cada respuesta con cambios se sube sola a GitHub (hook Stop → `scripts/autopush.sh`); no hace falta hacer commit manual.
