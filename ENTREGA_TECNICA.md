# Entrega técnica — OrbitLens SPHEREx

## Bloque vigente: operación y catálogo, pipeline 0.1.5

166 pruebas Python, 30 E2E, Ruff/build correctos. Se añaden cuotas por IP y
cadena de proxies, snapshots/recuperación y posición de cola, presupuesto temporal
cooperativo con Retry-After, descarga global acotada, límites de cuerpo SIA,
temporales únicos, validación de metadata FITS/SIA y checksum de caché original.
LRU conservador de caché y comprobación de disco; resultados/manuales protegidos.

Importación de secuencias locales sin red e índice de presets validados por
centro/integridad, con enlaces desde la UI y método visible. Docker/Compose,
arranque de producción y CI preparados; **no se ha construido Docker ni se ha
publicado en un hosting**. Ver `DEPLOYMENT.md` para límites y aceptación pendiente.

SIMBAD Harvard proporcionó catálogo/PM con bibliografía y metadata de época.
Se corrigieron centros a J2026; la auditoría anterior detectó Barnard/WISE 0855
fuera de sus salidas de 4′. Los 15 frames seleccionados nuevos contienen la
posición predicha, no una detección confirmada. Cuatro paquetes SIA partial +
R Dra local explícito; ver `ASTROMETRIA.md` y `evidencias/astrometria/`.

Recorrido real desde formulario hasta tres frames, nueve descargas 200 y
reapertura del trabajo/resultado tras reinicio. Ensayo con caché SIA real;
intento anterior fallido por timeout conservado. Evidencia en `evidencias/operacion/`.
No se atribuye al equipo una validación científica, hosting o teléfono físico.

Las secciones siguientes conservan el historial de bloques anteriores.

## Bloque actual: integridad y adquisición real, pipeline 0.1.4

Contraste explícito y prioridades en `BRECHAS_REQUISITOS.md`. Se corrigen nombres
VOTable reales, errores HTTP 200, TTL de vacíos, estados parciales, validación de
hashes/rutas, candidatos sustitutos, deduplicación y conservación de originales.
124 pruebas Python y 30 E2E correctos; Ruff y build correctos. Un aviso de
deprecación Starlette/AnyIO permanece, sin fallos de pruebas.

Resultado real del tutorial `63aac406686a9d82`: dos frames alineados, partial
por overflow y cuatro recortes 503. En Edge: cambio de frame y seis descargas
200, reproducción deshabilitada por tener menos de tres frames. No cierra O4.
`scripts/verify_real_sequences.py` añade un recorrido reproducible por los cinco
campos y guarda estados/errores sin inventar éxitos. Presentación/video aplazados.

La adquisición posterior obtuvo tres frames en cada uno de los cinco campos:
15 originales contrastados con SIA/cabeceras y cinco secuencias reproducidas en
Edge, 45 artefactos HTTP 200. Todos partial por overflow/fallos; astrometría y
comparación espectral independiente pendientes. Fichas técnicas, tiempos,
centros enmascarados y manifiestos en `evidencias/irsa/five-fields/README.md`.

## Acceso real recuperado parcialmente (pipeline 0.1.3)

Se descargó de IBE un recorte DR1 real del tutorial oficial: 3 954 240 bytes,
IMAGE 12×12, VERSION 7.0.5, D1, OBSID `2025W18_1B_0074_2`. Se inspeccionaron
HDU, tiempos, WCS, unidades, FLAGS, λ/ancho y original SHA-256. Se publicó con
manifiesto y derivado y se abrió en Edge; la descarga original por API devolvió
200 con hash coincidente. Evidencia y comandos en `DATOS_REALES.md`.

La conexión sigue intermitente: sondas SIA/TAP/IBE 200 y S3 206, pero las cuatro
consultas de Epsilon Indi B agotaron tiempo. El campo del tutorial NO sustituye
los cinco objetivos. H1 se mantiene parcial, no bloqueado por ausencia total de
FITS. No hay afirmaciones de detección/movimiento ni cinco secuencias cerradas.

105 pruebas Python, Ruff y build frontend correctos. Se añadió lectura del
ancho espectral desde WCS-WAVE y evaluación en coordenada objetivo. El importador
local valida procedencia declarada, metadatos y pertenencia del objetivo al WCS;
permite usar recortes descargados por Data Explorer sin SIA.

## Bloque de apoyo al equipo (pipeline 0.1.2)

- 100 pruebas Python y Ruff; build React correcto.
- 28 pruebas Playwright/Edge reales, escritorio y viewport móvil en zona
  `America/Lima`, proveedor de búsqueda controlado y archivos sintéticos.
  Informe y capturas en `QA_EQUIPO.md` y `evidencias/qa/`.
- Fallo encontrado y corregido: ISO sin zona se mostraba cinco horas desplazado;
  salida UTC explícita y compatibilidad del visor con manifiestos previos.
- Aplicación de tutoriales IRSA: VERSION de PRIMARY, detector numérico,
  WCS espectral sin SIP preservando WCS celestial. Regresiones añadidas.
- Recursos del reto reconsultados en Edge e integrados como enlaces explícitos;
  WiseView recibe coordenadas/FOV sin mezclar datos de misiones.
- Guion, créditos y borrador de submission preparados con asistencia de IA,
  sin atribuir aprobación a compañeros. No hay video grabado ni submission enviada.
- Recorte DR1 del tutorial intentado por IBE: HTTP 503; sin archivo real.
  Abrir WiseView desde Edge agotó conexión; no se verificaron imágenes externas.

Los bloques siguientes preservan la evidencia de versiones anteriores, no las
cifras vigentes. H1 y la validación real de los cinco campos siguen abiertos.

## Actualización: Epsilon Indi B y detector (pipeline 0.1.1)

Corrección de RA y selección estricta, pruebas y entrega a Dany/Terán en
[CORRECCIONES_QA.md](CORRECCIONES_QA.md). Suite actual: 94 pruebas; Ruff y build
frontend correctos. La evidencia de 76 pruebas de abajo corresponde a la base
0.1.0 y se conserva como registro histórico.

Reintento real con RA corregida, D2, `MAXREC=5`, timeout de lectura 15 s y un
intento por colección: DR1/DR1 deep timeout, QR3/QR3 deep HTTP 502. Sin FITS real
ni H1 cerrado. El verificador produce ahora manifiesto y original/derivado
indexados cuando logra el recorrido completo; el contrato se probó con fixtures.

Registro de ejecución de la implementación de Jesús. Complementa
[README.md](README.md) y [PROTOCOLO_CONSTRUCCION.md](PROTOCOLO_CONSTRUCCION.md).
No sustituye la revisión científica de Jordi ni el QA de Dany.

## 1. Base y entorno

| Dato | Valor |
| --- | --- |
| Repositorio | `orbitlens-spherex-of-final/orbitlens-spherex-ofi` |
| Commit base documental | `d7320` (`docs: actualizar plan DR1 QR3 y protocolo de construccion`) |
| Fecha de ejecución | 2026-11-14 |
| Sistema | Windows (PowerShell) |
| Python | 3.12.7 (venv local `.venv`) |
| Node / npm | 26.13.0 / 11.20.0 |
| Astropy | 7.0.0 |
| NumPy | 2.2.1 |
| reproject | 0.14.0 |
| FastAPI | 0.115.6 |
| Pillow | 11.1.0 |
| httpx | 0.28.1 |
| Ruff | 0.17.5 |

El commit base solo contenía documentación. La aplicación de esta entrega es una
implementación nueva, construida siguiendo el protocolo, no una recuperación del
código histórico descrito en `PLAN.md`.

## 2. Comandos ejecutados y resultados

### 2.1 Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm --prefix frontend install
```

Resultado: instalación correcta. `npm install` informó 71 paquetes, 0
vulnerabilidades y un aviso de script de instalación de `esbuild` (no bloqueante;
el build se completó).

### 2.2 Pruebas backend

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest
```

Resultado: **76 passed, 1 warning** en ~4.7 s. El aviso es una deprecación de
`anyio` dentro de `starlette/testclient.py`, no un fallo del proyecto.

Cobertura de la suite:

- coordenadas decimales, sexagesimales, rangos y valores no finitos;
- presets y alias;
- parser VOTable, deduplicación, reintentos y validación de host de cutout;
- máscaras `MSKN*`/`MSKD*` y política sin definiciones;
- FITS 2D, WCS, reproyección, estiramiento, colormap y escritura PNG/FITS;
- manifiesto atómico, SHA-256 y validación de esquema;
- cola de trabajos, deduplicación, capacidad y errores;
- contratos HTTP, validación de entradas, rutas de archivos y path traversal.

Ninguna prueba usa red ni datos reales de SPHEREx.

### 2.3 Linter

```powershell
.\.venv\Scripts\python.exe -m ruff check .
```

Resultado: **All checks passed**. Se corrigieron imports, anotaciones y un
`Path` no importado detectado en `service.py`; no se cambió comportamiento.

### 2.4 Build frontend

```powershell
npm --prefix frontend run build
```

Resultado: `tsc --noEmit` sin errores y `vite build` correcto. Salida en
`frontend/dist` (HTML + CSS + JS). `frontend/dist` está ignorado por Git; debe
reconstruirse en cada despliegue.

### 2.5 Arranque y smoke HTTP

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8010 --workers 1
```

Resultados observados:

- `GET /api/health` → 200, `status=ok`, versión `0.1.0`, cuatro colecciones
  (`spherex_dr1`, `spherex_qr3`, `spherex_dr1_deep`, `spherex_qr3_deep`).
- `GET /api/presets` → 200, `count=5`.
- `GET /` → 200, `text/html`, sirve el build de React.
- `GET /?result=<id>` → 200, la SPA carga el manifiesto por API.

### 2.6 Contrato resultado → manifiesto → archivos

Se generó un resultado sintético con:

```powershell
.\.venv\Scripts\python.exe scripts\make_demo_result.py
```

Identificador determinista: `5e1c78336933afa7`.

Verificado con el servidor real:

| Comprobación | Resultado |
| --- | --- |
| `GET /api/results/5e1c78336933afa7/manifest` | 200, 8 frames, 16 archivos |
| SHA-256 de los 16 archivos contra el manifiesto | 0 discrepancias |
| `GET .../files/01_demo-png` | 200, `image/png`, 29 795 bytes |
| `GET .../files/01_demo-fits` | 200, `application/fits`, 43 200 bytes |
| PNG y FITS legibles | Sí (FITS derivado 98×98) |

**Este resultado es sintético y está etiquetado como tal en el manifiesto y en la
interfaz.** No demuestra que el pipeline funcione con datos reales de SPHEREx.

## 3. Prueba real contra IRSA — bloqueada

Objetivo de prueba: Estrella de Barnard, RA 269.452080, Dec 4.693390, FOV 10′.

```powershell
.\.venv\Scripts\python.exe scripts\verify_real_data.py --target barnard --maxrec 5
```

Resultado:

```text
Colecciones: ['spherex_dr1', 'spherex_qr3', 'spherex_dr1_deep', 'spherex_qr3_deep']
Registros: 0  overflow=False
AVISO: SIA spherex_dr1: The read operation timed out
AVISO: SIA spherex_qr3: timed out
AVISO: SIA spherex_dr1_deep: [Errno 11001] getaddrinfo failed
AVISO: SIA spherex_qr3_deep: [Errno 11001] getaddrinfo failed
No se descargó nada: la consulta no devolvió imágenes.
```

Sondas directas con `curl.exe`:

| URL | Resultado |
| --- | --- |
| `https://irsa.ipac.caltech.edu/Missions/spherex.html` | 200, 9 985 bytes |
| `https://irsa.ipac.caltech.edu/SIA?...` | **502 Proxy Error**, 341 bytes |
| `https://irsa.ipac.caltech.edu/SIA` (sin parámetros) | **502 Proxy Error** |
| `https://irsa.ipac.caltech.edu/TAP/sync?...` | **502 Proxy Error** |
| `http://irsa.ipac.caltech.edu/SIA?...` | 301 → HTTPS |
| Reintentos SIA (3) | timeout, DNS fallido, 502 |

Cuerpo del 502: «The proxy server received an invalid response from an upstream
server… Error reading from remote server». El DNS resolvió
`irsa.ipac.caltech.edu → irsaproxy1.ipac.caltech.edu → 134.4.54.42` en una
consulta, y falló en otra.

Conclusión: **el bloqueo es externo al código**. No se descargó ningún FITS real
ni se inspeccionaron HDU, unidades, tiempos, WCS o máscaras reales. Por eso:

- **H1 no se declara completado.**
- No se afirma cobertura ni detección de ninguno de los cinco objetos.
- Los presets siguen marcados `verified=False`.

El cliente ya incorpora reintentos con backoff exponencial, timeouts
configurables, validación de host, límite de tamaño y comprobación de que el
contenido descargado sea FITS. Cuando IRSA vuelva a responder, el comando
`verify_real_data.py --download` es el siguiente paso para cerrar H1.

## 4. Riesgos y pendientes

| Riesgo / pendiente | Estado |
| --- | --- |
| IRSA SIA/TAP con 502 y DNS intermitente | Bloqueo externo; reintentar más tarde |
| Sin FITS real inspeccionado en esta copia | H1 abierto |
| Presets con coordenadas J2000 aproximadas | Requieren revisión de Jordi |
| Resultado sintético | Solo para QA de UI; nunca presentarlo como dato |
| `frontend/dist` ignorado | Reconstruir antes de desplegar |
| Un solo worker | Obligatorio por cola/caché en memoria |
| Despliegue público | No realizado en esta entrega |
| QA visual en navegador real | Pendiente de Dany |

## 5. Reproducción mínima para el equipo

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm --prefix frontend install
npm --prefix frontend run build
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\make_demo_result.py
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
```

Abrir el enlace `/?result=<id>` que imprime el generador sintético. Para datos
reales, ejecutar `scripts/verify_real_data.py` cuando IRSA esté disponible.
