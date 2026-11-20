# convert-img · Manual de uso

Aplicación web para convertir imágenes. Hace cuatro tipos de trabajo:

| Botón | Qué hace | Salida |
|---|---|---|
| **HEIC a JPG** | Pasa fotos de iPhone (HEIC/HEIF) a JPG estándar | `nombre_JPG.jpg` |
| **PNG a CMYK** | Convierte PNG a CMYK para imprimir en papel de diario | `nombre_CMYK.tif` |
| **JPG a CMYK** | Igual que PNG a CMYK, pero partiendo de JPG | `nombre_CMYK.tif` |
| **Marca de agua** | Superpone tu logo sobre las fotos (JPG, PNG o HEIC) | `nombre_WM.jpg` o `nombre_WM.png` |

Todo se procesa en la sesión de la app: los archivos no se guardan en ningún lado.

---

## 1. Elegir el idioma

Arriba a la derecha hay un selector con dos opciones: **🇪🇸 Español** (por defecto) y **🇬🇧 English**. El cambio es inmediato y traduce toda la pantalla.

> En Windows, los emojis de bandera pueden verse como las letras "ES" y "GB". Es solo un tema visual.

## 2. Elegir la conversión

Toca uno de los cuatro botones de arriba. El botón seleccionado queda resaltado. Al cambiar de conversión se limpian los archivos subidos y los resultados anteriores.

## 3. Paso 1 · Sube tus archivos

- Arrastra los archivos a la zona punteada o haz clic para elegirlos. Puedes subir **varios a la vez**.
- Formatos aceptados:
  - HEIC a JPG: `.heic`, `.heif`
  - PNG a CMYK: `.png`
  - JPG a CMYK: `.jpg`, `.jpeg`
  - Marca de agua: `.jpg`, `.jpeg`, `.png`, `.heic`, `.heif`
- Tamaño máximo: **200 MB por archivo**.
- Tamaño máximo del lote: **1000 MB (1 GB) en total** por tanda. Debajo del cargador se ve cuánto lleva el lote. Al llegar al 80% aparece un **aviso**; si se pasa del tope, aparece un error y el botón Convertir queda desactivado hasta que quites archivos o los conviertas en varias tandas.

### Opciones de HEIC a JPG
- **Calidad del JPG** (50% a 100%, por defecto 92%). Más calidad = archivo más pesado. Desde 90% la imagen conserva el máximo detalle de color.
- Se conservan los datos EXIF (fecha, cámara, etc.) y el perfil de color. La orientación se corrige sola: las fotos tomadas en vertical salen derechas.

### Opciones de PNG a CMYK y JPG a CMYK
Al elegir estas conversiones aparecen dos opciones:

**Perfil de conversión.** Es la "receta" que traduce los colores de pantalla (RGB) a tintas de imprenta (CMYK) para papel de diario. Son perfiles WAN-IFRA (norma ISO 12647-3). El número (TIC) es el máximo de tinta total que admite el perfil:

| Perfil | Cuándo usarlo |
|---|---|
| **TIC 220** (recomendado, viene seleccionado) | El estándar para diario. Úsalo salvo que tu imprenta indique otra cosa. |
| **TIC 200** | Papel de diario más liviano, para evitar que la tinta se transparente del otro lado. |
| **TIC 180** | Papel muy liviano. Usa menos tinta y los colores salen algo más apagados. |

> Consulta con tu imprenta qué TIC corresponde a su papel. Es el dato que más importa.

**Umbral de negro puro** (0% a 15%, por defecto 5%). Los píxeles negros o casi negros pasan a **negro puro**: solo tinta K al 100%, sin cian, magenta ni amarillo. Esto asegura que textos y líneas finas imprimen con una sola tinta, sin problemas de registro.

- Con **5%** se cubren los negros "casi negros" (por ejemplo #0A0A0A) y el ruido de compresión de los JPG.
- Con **0%** solo el negro exacto (RGB 0,0,0) pasa a negro puro.
- No subas el valor de más: los grises oscuros reales empiezan a perder detalle.

Los colores que no son negro conservan su mezcla de tintas según el perfil elegido.

### Opciones de Marca de agua
1. **Sube la marca de agua** en el segundo cargador. Puede ser PNG, JPG o WEBP; lo ideal es un **PNG con fondo transparente**. La marca **no queda guardada**: hay que subirla cada vez que se abre la app. Sin marca, el botón Convertir queda desactivado.
2. **Posición:** abajo a la derecha (por defecto), abajo a la izquierda, arriba a la derecha, arriba a la izquierda o centro.
3. **Tamaño** (5% a 100% del ancho de la foto, por defecto **10%**).
4. **Opacidad** (10% a 100%, por defecto **20%**). Con 100% la marca queda sólida; con valores bajos se ve la foto a través del logo.
5. **Calidad del JPG** (50% a 100%, por defecto **85%**). Solo afecta a las salidas JPG. Con 100% los archivos pesan 3 a 5 veces más sin ganar calidad real, porque la foto original ya venía comprimida.
6. **Autor** y **Copyright** (opcionales). Se escriben en los metadatos (EXIF) de cada foto, de forma invisible. Al subir la marca, **Autor** se rellena con el nombre del archivo de la marca (sin extensión) y **Copyright** con ese mismo nombre detrás de un **©** fijo; ambos se pueden editar. Si se dejan vacíos, no se escribe nada.

Cómo sale el resultado:
- Las fotos **PNG** salen en **PNG** y las **JPG/HEIC** en **JPG**. Se respeta la orientación de cada foto y se conserva el perfil de color.
- Los metadatos se guardan como texto simple: el **©** queda como **(c)** y se quitan los acentos (José pasa a Jose), para que ningún programa lo muestre roto.
- La marca de agua visible es parte de la imagen. Los metadatos son un respaldo invisible: se pueden borrar.

## 4. Paso 2 · Convierte

1. Pulsa **Convertir**.
2. Una barra de progreso muestra el archivo actual, el porcentaje y el tiempo estimado que falta.
3. Si un archivo está dañado o no es válido, se marca con error y **la conversión continúa** con los demás.

## 5. Paso 3 · Descarga

- Arriba aparecen tres contadores: **Convertidos**, **Errores** y **Tiempo**.
- **Descargar todo (.zip)** baja todos los archivos convertidos en un único archivo comprimido.
- Cada fila tiene su propio botón **Descargar** (hasta las primeras 100 filas; el resto se baja por el .zip).
- Los archivos se guardan en la carpeta **Descargas** de la computadora donde corre tu navegador.
- **Limpiar y empezar de nuevo** borra los resultados y vacía la zona de carga.

### Nombres de salida
Se toma el nombre original y se agrega un sufijo: `foto.heic` → `foto_JPG.jpg`, `afiche.png` → `afiche_CMYK.tif`, y con marca de agua `foto.jpg` → `foto_WM.jpg`, `afiche.png` → `afiche_WM.png`. Si dos archivos darían el mismo nombre, el segundo lleva un número: `foto_JPG (2).jpg`.

---

## 6. Qué esperar del resultado CMYK

- El archivo es un **TIFF CMYK** sin pérdida (8 bits por canal, compresión Deflate), con el **perfil ICC incrustado**. Los programas de diseño e imprentas lo leen sin configuración extra.
- Se **conservan los DPI** de la imagen (300 si no traía).
- Las zonas **transparentes** se aplanan sobre **fondo blanco**.
- En los JPG se **aplica la orientación** guardada por la cámara.
- Los **colores se ven más apagados que en pantalla**. Es normal: la tinta de imprenta, y más sobre papel de diario, no llega a los colores brillantes de una pantalla. El perfil busca mantenerlos lo más vivos posible sin pasarse de tinta.
- Muchos visores (el del navegador, por ejemplo) no abren TIFF. Para revisar el resultado usa Photoshop, Affinity, GIMP, Acrobat o el visor de tu sistema.

## 7. Preguntas frecuentes

**¿Por qué la extensión dice `.tif` y no `.cmyk`?**
CMYK es el espacio de color, no un formato de archivo. El archivo es un TIFF con los píxeles guardados en CMYK. TIFF es de los formatos más usados en imprenta.

**¿Se puede guardar CMYK en PNG?**
No. PNG solo admite grises y RGB.

**El negro no sale negro puro.**
Sube un poco el umbral de negro puro (por ejemplo a 8%) si tus negros son más claros que #0D0D0D.

**Los colores salen apagados.**
Es lo esperado en CMYK y en papel de diario. Para comparar con lo que va a salir impreso, pide una prueba a la imprenta.

**Un archivo da error.**
Revisa que el archivo no esté dañado y que tenga el formato que corresponde a la conversión elegida. Los demás archivos del lote se convierten igual.

**Las fotos con marca de agua pesan mucho más que el original.**
Casi siempre es la calidad del JPG. Déjala en 85% (valor por defecto): con 100% el archivo se multiplica por 3 o más.

**La marca de agua no se ve.**
Sube la opacidad o el tamaño, y usa un PNG cuyos colores contrasten con la foto. Con 20% de opacidad una marca oscura sobre una foto oscura casi no se nota.

**¿Se puede quitar la marca de agua?**
No con un ajuste: queda dibujada en los píxeles. Con edición manual se puede disimular, sobre todo si es chica y está en una esquina. Es una señal de autoría, no una protección total.

**¿Hay límite de conversiones?**
Por defecto no. Si se activó la versión gratuita, un medidor muestra cuántas conversiones llevas usadas, y al llegar al límite aparece un aviso para pasar a la versión PRO.

**¿Cuántos archivos puedo subir de una vez?**
No hay tope de cantidad, pero sí de peso: 1000 MB por lote (configurable). Además depende de la memoria del servidor: los archivos se procesan en memoria. Si la app se pone lenta o se corta, divide el trabajo en lotes más chicos.
