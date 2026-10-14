# convert-img · Documentación técnica

## 1. Resumen

App **Streamlit** (Python) con tres conversiones de imágenes: HEIC→JPG y PNG/JPG→CMYK (TIFF con perfil ICC WAN-IFRA para papel de diario). La lógica de conversión está separada de la interfaz y se prueba con pytest. Interfaz bilingüe (español por defecto, inglés).

| Componente | Detalle |
|---|---|
| Lenguaje | Python 3.12 (el CI usa 3.12) |
| Interfaz | Streamlit `>=1.43,<2` |
| Imágenes | Pillow `>=10.4` (incluye `ImageCms`/LittleCMS), pillow-heif `>=0.18`, numpy `>=1.26` |
| Tests | pytest (22 tests) |
| CI | GitHub Actions: tests en cada push a `main` y en cada PR |

## 2. Estructura del repositorio

```
app.py                  Interfaz Streamlit (solo UI)
converters.py           Lógica de conversión (sin importar streamlit)
licensing.py            Contador de conversiones y límite opcional
profiles/               Perfiles ICC CMYK
tests/test_converters.py
docs/                   Manual de uso y esta documentación
assets/                 logo.png, favicon.png
.streamlit/config.toml  Tema y límite de subida
.streamlit/secrets.toml.example
.github/workflows/ci.yml
.claude/settings.json + scripts/autopush.sh   Hook de Claude Code
.devcontainer/          Entorno de desarrollo
```

### Perfiles ICC (`profiles/`)
| Archivo | Nombre interno | Uso |
|---|---|---|
| `WANIFRA_NP26_TIC220.icc` | ICONSnewspaper26v5_1 | Modo `*220` (por defecto, recomendado por WAN-IFRA) |
| `WANIFRA_NP26_TIC200.icc` | ICONSnewspaper26v5_200 | Modo `*200` |
| `WANIFRA_NP26_TIC180.icc` | ICONSnewspaper26v5_180 | Modo `*180` |
| `ISOnewspaper26v4.icc` | ISOnewspaper26v4 | **No se usa** (queda guardado como alternativa) |

Todos son perfiles de salida CMYK, versión ICC 2.4. Los de WAN-IFRA siguen ISO 12647-3:2013.

## 3. `converters.py`

### 3.1 Modos (`MODES`)
`Mode` es un `dataclass` inmutable con: `key`, `label`, `subtitle`, `noun`, `in_exts`, `out_ext`, `out_label`, `mime`, `out_suffix` y `profile`.

- `heic`: entrada `heic/heif`, salida `.jpg`, sufijo `_JPG`.
- `png220`, `png200`, `png180` y `jpg220`, `jpg200`, `jpg180`: se generan en un bucle. Entrada `png` o `jpg/jpeg`, salida `.tif`, sufijo `_CMYK`, `profile` = archivo `.icc` de `profiles/`.

### 3.2 `convert(mode, data, quality=92, black_pct=0) -> bytes`
Punto de entrada. Despacha a `heic_to_jpg` si el modo es `heic`, o a `png_to_cmyk_tiff` si el modo tiene perfil. Un modo desconocido lanza `ValueError`.

### 3.3 `heic_to_jpg`
1. Calidad acotada a 30–100.
2. Abre con Pillow (pillow-heif registrado) y carga la imagen.
3. pillow-heif ya aplica la rotación, así que se fuerza `Orientation = 1` en el EXIF para no rotar dos veces.
4. Conserva EXIF y perfil ICC; guarda JPEG con `optimize=True` y submuestreo 4:4:4 si la calidad es ≥ 90 (si no, 4:2:0).

### 3.4 `png_to_cmyk_tiff(data, chunk_rows=512, black_pct=0, profile="")`
Se usa para PNG y para JPG.

1. **Lectura:** se guardan los DPI (300 si no hay) y el perfil ICC incrustado (solo si la imagen es RGB/RGBA). Luego `ImageOps.exif_transpose` aplica la orientación EXIF (relevante en JPG).
2. **Normalización:** `_to_8bit_rgba` pasa grises de 16 bits a 8 bits y todo a RGBA.
3. **Procesamiento por bloques** de `chunk_rows` filas (512) para no duplicar la memoria en imágenes grandes. En cada bloque:
   - Se aplana la transparencia sobre blanco: `rgb = c·a + 255·(1−a)`.
   - **Con perfil:** el bloque se convierte con `ImageCms.applyTransform`.
   - **Sin perfil** (modo matemático, usado solo por los tests): `K = 255 − max(R,G,B)` y `C,M,Y = (max − canal) / max · 255`.
4. **Regla de negro puro:** los píxeles con `max(R,G,B) <= black_max` se fuerzan a `(C,M,Y,K) = (0,0,0,255)`. `black_max = round(black_pct / 100 · 255)`. Con perfil, el negro exacto (RGB 0,0,0) también se fuerza aunque `black_pct` sea 0.
5. **Salida:** TIFF CMYK, compresión `tiff_adobe_deflate`, DPI de origen y, con perfil, el ICC incrustado (`icc_profile=`).

### 3.5 Transformación de color (`_transform`)
- Perfil de origen: el ICC incrustado en la imagen si es RGB y se puede leer; si no, **sRGB**.
- Perfil de destino: el `.icc` del modo.
- Intención: **colorimétrico relativo** con **compensación de punto negro** (`BLACKPOINTCOMPENSATION`).
- La transformación y los bytes del perfil se cachean con `functools.lru_cache`, así no se vuelven a construir por cada archivo (los perfiles pesan de 0,8 a 2,5 MB).

### 3.6 Otras funciones
- `accepted_types(mode)`: lista de extensiones para el cargador de archivos.
- `output_name(filename, mode, taken)`: nombre de salida con sufijo y extensión; evita choques con `name (2).ext`, comparando en minúsculas.

## 4. `app.py` (interfaz)

### 4.1 Flujo
1. **Estado** (`st.session_state`): `mode` (`heic`/`png`/`jpg`), `tic` (`220`/`200`/`180`), `lang`, `uploader_n`, `result`, `show_pro`.
2. El modo real de conversión se arma como `cmode = "heic"` o `f"{mode}{tic}"` (por ejemplo `png220`).
3. **Selector de idioma** (`st.segmented_control`) arriba a la derecha; al cambiar se guarda en `ss.lang` y se hace `rerun`.
4. **Tres botones de modo** (`mode_heic`, `mode_png`, `mode_jpg`). `set_mode` limpia el resultado y reinicia el cargador de archivos (cambiando su `key` con `uploader_n`).
5. **Paso 1:** `st.file_uploader` con las extensiones de `cmode`. HEIC muestra el slider de calidad; PNG y JPG muestran el selector de perfil (`st.radio` horizontal), una nota y el slider de umbral (0–15, por defecto 5).
6. **Paso 2:** botón Convertir, que recorre los archivos uno a uno, actualiza la barra de progreso con tiempo estimado y captura los errores por archivo sin detener el lote. Cada conversión exitosa llama a `lic.consume`.
7. **Paso 3:** se arma un `.zip` en memoria y se muestran contadores, descarga general y una fila por archivo (botón individual solo en las primeras `MAX_ROWS_WITH_BUTTON = 100`).

### 4.2 Textos e idiomas
Todos los textos visibles están en el diccionario `TEXTS` (`"es"` y `"en"`) y se leen con `t(clave, **valores)`. **Al agregar un texto, hay que agregarlo en los dos idiomas.** El panel Admin queda en inglés a propósito.

### 4.3 Estilos
CSS embebido en `app.py`. Los botones de modo se estilizan con el selector `[class*="st-key-mode_"]`, que alcanza a todos los botones cuya clave empieza con `mode_` (función de Streamlit ≥ 1.43).

### 4.4 Resultados
`ss.result` guarda `grp` (el grupo: `heic`, `png` o `jpg`), `mode` (el modo real), la lista de archivos, el `.zip` y las estadísticas. El resultado se muestra mientras el grupo coincida con el modo elegido, y se puede cambiar de perfil sin perderlo.

## 5. `licensing.py`

Contador de archivos convertidos con límite opcional. Es un freno básico, no un sistema de licencias.

| Variable de entorno | Efecto |
|---|---|
| `CONVERT_IMG_LIMIT` | Límite de conversiones. `0` (por defecto) = sin límite, solo se cuenta. |
| `CONVERT_IMG_COUNTER` | `file` (por defecto en `app.py`): contador firmado en disco, global. `session`: por sesión del navegador. |
| `CONVERT_IMG_SECRET` | Clave HMAC con la que se firma el contador. |

- `MemoryStore`: contador en un diccionario (`st.session_state`).
- `FileStore`: dos copias firmadas con HMAC-SHA256 (`~/.convert-img/usage.json` y `.usage.json` en la carpeta de la app). Al leer se toma el mayor valor entre las copias con firma válida.
- `info`, `consume`, `reset`: lectura, suma de una conversión y reinicio. `consume` devuelve `False` si hay límite activo y ya se alcanzó.

**Secrets opcionales** (Streamlit Secrets o variables de entorno): `ADMIN_KEY` habilita el panel Admin en la barra lateral (total convertido y reinicio del contador). `PRO_URL` agrega el botón "Obtener la versión PRO" en el aviso de límite.

## 6. Configuración (`.streamlit/config.toml`)
Tema claro con los colores de la marca (`#1f9bb0`, `#0f2b46`, fondo `#f3f6f9`), `maxUploadSize = 200` (MB por archivo), barra de herramientas mínima y sin estadísticas de uso.

## 7. Tests

```bash
pip install pytest
python -m pytest -q tests        # 22 tests
```

Cubren: colores primarios y conversión matemática, transparencia sobre blanco, DPI, PNG de paleta/gris/16 bits, procesamiento por bloques (mismo resultado con cualquier tamaño de bloque, con y sin perfil), umbral de negro puro, los tres perfiles ICC (negro en K puro, blanco sin tinta, perfil incrustado, tinta total dentro del límite), JPG (extensiones, negro con ruido de compresión, orientación EXIF), HEIC (calidad, EXIF, orientación), nombres de salida y colisiones, y el contador (memoria, archivo, manipulación de una copia).

El CI (`.github/workflows/ci.yml`) los corre en Python 3.12 en cada push a `main` y en cada pull request.

## 8. Ejecución y despliegue

**Local:**
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

**Streamlit Community Cloud:** repositorio `convert-img`, rama `main`, archivo `app.py`, Python 3.12. Redeploya solo con cada push a `main`. Tiene unos ~1 GB de RAM compartida: conviene procesar lotes moderados.

**Otras opciones** (Cloud Run, AWS App Runner/ECS): requieren agregar un `Dockerfile`. Puntos a tener en cuenta:
- Cloud Run rechaza por defecto peticiones de más de 32 MB: hay que habilitar HTTP/2.
- Streamlit necesita WebSockets y conviene afinidad de sesión.
- El contador en archivo no persiste entre instancias; habría que moverlo a una base de datos.

## 9. Flujo de desarrollo

- Los cambios se hacen en una rama, se abre un pull request y se **fusiona en `main`** (squash).
- Antes de terminar un cambio: `python -m pytest -q tests`.
- Hook de Claude Code (`.claude/settings.json` → `scripts/autopush.sh`): al terminar cada respuesta con cambios, hace commit y push automáticos con el mensaje "Actualización AAAA-MM-DD HH:MM". Para desactivarlo, renombrar `.claude/settings.json`.

### Cómo agregar una conversión
1. Escribir la función en `converters.py` (sin importar streamlit).
2. Agregar la entrada en `MODES` y en `convert()`.
3. Escribir tests en `tests/`.
4. En `app.py`: agregar el ícono en `ICONS`, los textos (`*_label`, `*_sub`, `*_title`, `*_lead`) en **ambos** idiomas de `TEXTS`, y el botón en el bucle de modos. Si la conversión usa perfiles, revisar la construcción de `cmode`.

## 10. Límites conocidos y pendientes

- **Memoria:** cada archivo se procesa completo en memoria. El procesamiento por bloques reduce el consumo en la conversión de color, pero la imagen entera se carga.
- **Color:** la conversión con ICC no equivale a una prueba de imprenta calibrada. Los colores muy saturados quedan fuera del rango de la tinta y se acercan al más parecido (colorimétrico relativo).
- **JPG ya en CMYK:** se convierte con la regla por defecto de Pillow (sin perfil de origen).
- **Contador:** por defecto, `app.py` usa el contador en archivo (global); el texto de cabecera de `licensing.py` dice que es `session`. Conviene alinear ambos. En una app pública, el contador global no es un límite por usuario.
- **README:** quedó desactualizado en dos puntos (dice "interfaz en inglés" y "límite de 300 conversiones", y hoy la interfaz es bilingüe y no hay límite por defecto).
- **Licencia de los perfiles ICC:** revisar que la licencia de WAN-IFRA permita redistribuirlos en el repositorio si este deja de ser privado.
- **`ISOnewspaper26v4.icc`:** incluido pero sin uso.
