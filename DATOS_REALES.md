# Datos reales IRSA — primer recorte verificado, 2026-11-14

## Estado vigente: pipeline 0.1.5, centros J2026 y operación

**Corrección importante:** el catálogo/PM mostró que Barnard y WISE 0855 no
quedaban dentro de sus recortes anteriores de 4′. Las secciones posteriores
son historial; usar los centros y los IDs nuevos de [ASTROMETRIA.md](ASTROMETRIA.md).
Hay tres frames por campo en la selección actual: cuatro paquetes SIA partial
y R Draconis importado explícitamente de originales D6 existentes. Posiciones
predichas dentro de los 15 frames; no implica detección ni píxel válido.

La UI ofrece abrir los resultados guardados si existe `data/presets.json`:

```powershell
.\.venv\Scripts\python.exe scripts\index_presets.py --report data\real-data\selected-corrected-fields.json
```

La nueva ruta sin red usa `scripts/import_irsa_sequence.py --index ARCHIVO.json`;
exige 2–16 MEF del mismo detector, metadatos completos, fuente DR1/QR3 declarada,
hashes opcionales de entrada y tiempos finitos. No infiere wide/deep ni autentica
el operador. Comparte máscara, reproyección, escala y publicación con el servicio.

Recorrido real desde formulario y recuperación tras reinicio comprobados en
`evidencias/operacion/live-http.json` (SIA real en caché; recortes descargados).
Se conserva también un intento anterior con timeout, sin declararlo vacío.
Para reproducir explícitamente con red, desde `frontend/`:
`node e2e/live-check.mjs`. No forma parte del CI ni demuestra hosting público.

## Resultado más reciente: cinco secuencias reales parciales

La ejecución posterior del nuevo script consiguió tres frames para **cada uno
de los cinco campos**. Los 15 originales coinciden en OBSID/detector/VERSION y
MJD con sus manifiestos/SIA. Se abrieron los cinco resultados en Edge, se probó
reproducción/pausa y se descargaron los 45 artefactos con HTTP 200.

IDs, intervalos, λ, máscaras, tiempos, capturas e informes:
[evidencias/irsa/five-fields/README.md](evidencias/irsa/five-fields/README.md).
Todos son `partial`: overflow y algunos recortes fallidos. Hay centros
enmascarados y λ distinta entre frames; los presets siguen `verified=False`.
Esto no valida astrometría ni confirma detecciones. Las secciones siguientes
conservan la progresión desde el campo del tutorial.

## Actualización: dos frames reales mediante SIA, pipeline 0.1.4

Se corrigió un fallo del parser: los FIELD de IRSA tienen IDs `col_*` y nombres
astronómicos distintos. Astropy debe usar `use_names_over_ids=True`. La respuesta
guardada en `data/real-data/sia-reference.vot` contiene tres filas reales y se
interpreta correctamente; no todo el bloqueo previo era de conectividad.

El pipeline consultó las cuatro colecciones y encontró 40 registros (MAXREC=20
por colección, búsqueda truncada), diez candidatos D1. Intentó seis recortes:
dos descargados y cuatro rechazados por 503. Generó `63aac406686a9d82`, estado
**partial**, con dos frames alineados, escala común y FITS originales/derivados.
Es el campo del tutorial, no uno de los cinco objetivos. Los dos frames son
exposiciones cercanas, no evidencia de variación ni movimiento.

Abrir <http://127.0.0.1:8000/?result=63aac406686a9d82> tras arrancar el servidor.
Se comprobó en Edge 157: cambio entre `2025W18_1B_0074_2` y
`2025W18_1B_0074_3`, reproducción deshabilitada, manifiesto y seis artefactos
con HTTP 200. Captura: `evidencias/irsa/real-two-frames-browser.png`.
El manifiesto conserva `code_commit=dev` de esa ejecución; no se reescribe la
evidencia para atribuirle posteriormente otro commit.

Para repetir el pipeline completo con informes persistidos:

```powershell
.\.venv\Scripts\python.exe -u scripts\verify_real_sequences.py --target reference --fov 1.2 --detector D1
.\.venv\Scripts\python.exe -u scripts\verify_real_sequences.py --target all --fov 4
```

Ver límites, estados y requisitos abiertos en `BRECHAS_REQUISITOS.md`.
La sección siguiente conserva la evidencia del primer recorte individual.

## Primer recorte individual (pipeline 0.1.3)

**Ya hay un recorte real DR1 descargado, abierto, procesado y servido en el
navegador.** No es sintético. Es el campo de referencia del tutorial Intro de
IRSA, **no Epsilon Indi B ni otro de los cinco presets**. Un único frame no es
una secuencia temporal ni acredita detección o movimiento.

## Abrir lo que ya tenemos en esta máquina

```powershell
npm --prefix frontend run build
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
```

Abrir <http://127.0.0.1:8000/?result=9362cdf8afb5c043>.
El visor muestra «Recorte individual», los metadatos y descargas de PNG,
FITS original y FITS alineado. Directorio: `data/results/9362cdf8afb5c043/`.

## Reproducir desde otra instalación

```powershell
$env:ORBITLENS_CODE_COMMIT = git rev-parse HEAD
.\.venv\Scripts\python.exe -u scripts\download_reference_cutout.py
```

Una petición a IBE descarga **solo un recorte** de 0.02 grados (1.2 arcmin),
no el padre de 60 MB. Luego se genera el manifiesto. Si ya existe el archivo
local, se valida/procesa sin consultar la red.

Procedencia publicada en el [tutorial oficial Intro, sección 5](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/):

```text
https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/level2/2025W18_1B/l2b-v27-2026-196/1/level2_2025W18_1B_0074_2D1_spx_l2b-v27-2026-196.fits?center=304.693508808,42.4436872991&size=0.02
```

## Inspección registrada

| Propiedad | Valor leído/calculado |
| --- | --- |
| Release | DR1 (ruta oficial); no se infiere wide/deep de la ruta |
| Centro solicitado ICRS | RA 304.693508808°, Dec +42.4436872991° |
| Original | 3 954 240 bytes; `IMAGE` 12×12, float32 |
| HDU | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| OBSID | `2025W18_1B_0074_2` |
| VERSION (PRIMARY) | `7.0.5` |
| Detector (IMAGE) | 1 → D1 |
| BUNIT | `MJy / sr` |
| DATE-OBS / MJD-OBS | 2025-04-29T00:24:27.897Z / 60794.016989549 |
| DATE-END | 2025-04-29T00:26:23.015Z |
| λ / ancho en coordenada solicitada, WCS-WAVE | 0.753036693 / 0.017555136 µm (aproximados) |
| Píxeles válidos de entrada, política actual | 98.61% |
| Píxeles válidos tras reproyección | 84.03%; centro válido |
| Original SHA-256 | `c320ddcdb677ed23168a6cf161272c508b0dd9c808c664cdc492608014570f58` |

La pérdida de cobertura tras reproyectar un recorte pequeño es esperable en
bordes y por la máscara conservadora; no es una medida de sensibilidad.
No se confirma la identidad de ninguna fuente del campo.

El FITS define los bits de FLAGS, incluido SOURCE=21. La política no descarta
SOURCE por sí solo; queda un aviso por SATELLITE_HALO no definido. No se
inventa ese bit. Se conserva SIP en el WCS celestial y se excluye del espectral.
El ancho de banda se obtiene del segundo eje WAVE-TAB cuando el WCS lo describe
como bandwidth. Son valores de visualización, no una calibración científica.

## Qué ocurrió con la conectividad

En una sonda acotada: SIA/TAP/IBE **200**, S3 Range **206** y listado S3 **200**.
Eso demuestra respuesta en esas peticiones, no estabilidad permanente. La
consulta posterior de Epsilon Indi B agotó los timeouts en las cuatro
colecciones. La descarga directa conocida del tutorial sí se completó.

Por tanto, no debemos seguir esperando a que una búsqueda grande funcione para
probar el lector: podemos procesar URLs verificadas o archivos descargados
manualmente. Cambiar a astroquery no elimina un fallo del mismo endpoint.

## Ruta para los cinco objetivos

1. Confirmar las coordenadas/época (en especial los objetos de alto movimiento
   propio). El preset sigue siendo una referencia aproximada.
2. Probar `verify_real_data.py --target epsindi_b --download --detector D2`
   con timeouts cortos y sin múltiples consultas simultáneas.
3. Si SIA sigue fallando, usar el [Data Explorer oficial](https://irsa.ipac.caltech.edu/applications/spherex):
   buscar la coordenada, elegir DR1/QR3 y un detector; descargar como **cutout
   MEF** y guardar la URL/procedencia. Preferir varias épocas del mismo campo,
   con λ/ancho documentados; mismo detector no garantiza misma λ.
4. Importar cada recorte local sin SIA:

```powershell
.\.venv\Scripts\python.exe scripts\import_irsa_cutout.py --fits RUTA_AL_RECORTE.fits --source-url URL_HTTPS_IRSA --ra RA_GRADOS --dec DEC_GRADOS --fov ANCHO_ARCMIN
```

El importador exige DR1/QR3 Level 2, OBSID, VERSION, unidades, detector y tiempo;
verifica que la coordenada esté dentro del FITS y conserva el original con hash.
La URL es una declaración de procedencia del operador, no una nueva consulta ni
una autenticación criptográfica del archivo.

S3 es una alternativa oficial documentada: bucket público `nasa-irsa-spherex`,
región us-east-1, sin credenciales. **Todavía no es un fallback integrado**.
Leer el padre completo contradiría nuestro límite: habría que implementar
lectura parcial por rangos y conservar bien WCS-WAVE/EPSF/FLAGS. No basta
añadir `?center=` a una URL S3, porque S3 no ejecuta el servicio de cutouts.

## Evidencia y límites

Captura de Edge real: `evidencias/irsa/real-dr1-browser.png`. El original se
recuperó vía API con HTTP 200, 3 954 240 bytes y hash coincidente. Se comprobó
la fecha UTC con navegador en `America/Lima`.

Los FITS viven en `data/` ignorado por Git; no se confunde la captura con datos
de entrada. `download_reference_cutout.py` permite recuperar el original de la
misma fuente y regenerar el resultado. Esto completa la primera lectura real,
pero **no las cinco secuencias ni su revisión astrométrica/científica**.
