# convert-img · by nosotros

Convertidor de imágenes en **Streamlit** con dos conversiones, elegibles con un botón:

- **HEIC to JPG** — fotos de iPhone a JPEG (conserva EXIF e ICC, corrige la orientación, calidad ajustable).
- **PNG to CMYK** — TIFF CMYK sin pérdida para papel de diario (8 bits/canal, Deflate; conserva los DPI; transparencias sobre blanco). Al elegirlo aparecen el perfil ICC WAN-IFRA de `profiles/` (TIC 220 recomendado por defecto, 200 y 180) y el umbral de negro puro, que se incrusta en el TIFF; el negro puro sale solo con tinta K.

Flujo: **Upload** de archivos → **Convert** (barra de progreso por archivo) → **Download** (un .zip o archivo por archivo;
el navegador los guarda en la carpeta *Descargas* de la computadora desde la que se usa la app).
Versión gratuita: límite de 300 conversiones, luego avisa para actualizar a PRO. Interfaz en inglés.

## Ejecutar en tu PC
    python -m venv .venv && .venv\Scripts\activate      # Windows  (Linux/Mac: source .venv/bin/activate)
    pip install -r requirements.txt
    streamlit run app.py

## Tests
    pip install pytest
    python -m pytest -q tests

## Estructura
| Archivo | Qué hace |
|---|---|
| `app.py` | Interfaz Streamlit (selector de modo, upload, progreso, descargas, medidor de licencia). |
| `converters.py` | Lógica de conversión pura (Pillow + pillow-heif + numpy). Sin Streamlit, testeable. |
| `licensing.py` | Contador de archivos convertidos (límite opcional) (por sesión o en archivo firmado). |
| `tests/` | Tests de pytest (conversión, colores CMYK, EXIF, DPI, límite). |
| `.streamlit/config.toml` | Tema (colores de la marca) y límite de subida (200 MB por archivo). |
| `.github/workflows/ci.yml` | Corre los tests en cada push. |
| `.claude/settings.json` + `scripts/autopush.sh` | Auto-commit y push a GitHub cuando Claude Code termina cada respuesta. |

## GitHub + auto-push con Claude Code (una sola vez)
1. Creá un repositorio vacío en GitHub (por ejemplo `convert-img`).
2. En esta carpeta:

       git init -b main
       git add -A
       git commit -m "Versión inicial"
       git remote add origin https://github.com/TU_USUARIO/convert-img.git
       git push -u origin main

3. Abrí Claude Code en la carpeta (`claude`) y aceptá el hook del proyecto. Desde ahí, cada vez que Claude termine
   una respuesta con cambios, se hace commit y push solo: **GitHub siempre tiene la última versión**.
   (Para desactivarlo, renombrá `.claude/settings.json`.)

## Deploy en Streamlit Community Cloud
1. Entrá a <https://share.streamlit.io> con tu cuenta de GitHub → **Create app**.
2. Elegí el repositorio `convert-img`, rama `main`, archivo principal `app.py`.
3. En **Advanced settings** elegí Python 3.12 (opcional: pegá los *Secrets* de abajo) → **Deploy**.
4. Streamlit vuelve a desplegar automáticamente con cada push a `main`: el flujo completo es
   *editar con Claude Code → push automático → app actualizada en 1-2 minutos*.

### Secrets opcionales (Settings > Secrets, ver `.streamlit/secrets.toml.example`)
- `ADMIN_KEY`: habilita un panel **Admin** (barra lateral) que muestra el total de archivos convertidos y permite reiniciar el contador.
- `PRO_URL`: agrega el botón "Get the PRO version" en el aviso de límite.

### Variables de entorno opcionales
- `CONVERT_IMG_LIMIT` (por defecto 0 = sin límite; poner p. ej. 300 para activar un límite) · `CONVERT_IMG_COUNTER` = `file` (por defecto, total global) o `session` · `CONVERT_IMG_SECRET`.

## Notas y límites
- **El contador** por defecto es *por sesión del navegador* (se reinicia al recargar). Con `CONVERT_IMG_COUNTER=file` se guarda en
  archivos firmados del servidor y es compartido por todos los usuarios: útil para una instalación local de una sola persona, no para
  una app pública. Es un freno básico; un límite sólido por usuario requiere login/licencias.
- **Memoria:** Streamlit Cloud tiene ~1 GB de RAM; los archivos se procesan en memoria, conviene lotes moderados.
- **CMYK:** conversión con perfil ICC (colorimétrico relativo + compensación de punto negro); el color puede diferir de una prueba de imprenta calibrada.
