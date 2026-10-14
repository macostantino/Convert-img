# convert-img · Manual de uso

Aplicación web para convertir imágenes. Hace tres tipos de conversión:

| Botón | Qué hace | Salida |
|---|---|---|
| **HEIC a JPG** | Pasa fotos de iPhone (HEIC/HEIF) a JPG estándar | `nombre_JPG.jpg` |
| **PNG a CMYK** | Convierte PNG a CMYK para imprimir en papel de diario | `nombre_CMYK.tif` |
| **JPG a CMYK** | Igual que PNG a CMYK, pero partiendo de JPG | `nombre_CMYK.tif` |

Todo se procesa en la sesión de la app: los archivos no se guardan en ningún lado.

---

## 1. Elegir el idioma

Arriba a la derecha hay un selector con dos opciones: **🇪🇸 Español** (por defecto) y **🇬🇧 English**. El cambio es inmediato y traduce toda la pantalla.

> En Windows, los emojis de bandera pueden verse como las letras "ES" y "GB". Es solo un tema visual.

## 2. Elegir la conversión

Toca uno de los tres botones de arriba. El botón seleccionado queda resaltado. Al cambiar de conversión se limpian los archivos subidos y los resultados anteriores.

## 3. Paso 1 · Sube tus archivos

- Arrastra los archivos a la zona punteada o haz clic para elegirlos. Puedes subir **varios a la vez**.
- Formatos aceptados:
  - HEIC a JPG: `.heic`, `.heif`
  - PNG a CMYK: `.png`
  - JPG a CMYK: `.jpg`, `.jpeg`
- Tamaño máximo: **200 MB por archivo**.

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
Se toma el nombre original y se agrega un sufijo: `foto.heic` → `foto_JPG.jpg`, `afiche.png` → `afiche_CMYK.tif`. Si dos archivos darían el mismo nombre, el segundo lleva un número: `foto_JPG (2).jpg`.

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

**¿Hay límite de conversiones?**
Por defecto no. Si se activó la versión gratuita, un medidor muestra cuántas conversiones llevas usadas, y al llegar al límite aparece un aviso para pasar a la versión PRO.

**¿Cuántos archivos puedo subir de una vez?**
Depende de la memoria del servidor: los archivos se procesan en memoria. Si la app se pone lenta o se corta, divide el trabajo en lotes más chicos.
