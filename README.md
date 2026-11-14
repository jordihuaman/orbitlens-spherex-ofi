# OrbitLens — SPHEREx

Herramienta web para construir **secuencias temporales de imágenes infrarrojas de
SPHEREx** a partir de una ascensión recta y una declinación. El backend consulta
las colecciones vigentes de IRSA (DR1 + QR3), descarga recortes FITS, los alinea
en una rejilla común y publica un manifiesto con PNG, FITS derivados y metadatos.
El frontend React reproduce la secuencia y muestra fechas, detector, cobertura,
máscaras y longitudes de onda.

> Una secuencia visual **no demuestra detección, movimiento propio ni
> variabilidad**. Los resultados son exploratorios y no sustituyen los FITS
> originales de IRSA.

## Estado verificado — 2026-11-14

Esta copia contiene una implementación nueva construida conforme a
[PROTOCOLO_CONSTRUCCION.md](PROTOCOLO_CONSTRUCCION.md). Lo comprobado en este
entorno es:

| Comprobación | Resultado |
| --- | --- |
| Suite Python (`pytest`) | **76 pruebas pasan** |
| Build frontend (`tsc --noEmit && vite build`) | Correcto, genera `frontend/dist` |
| Arranque `uvicorn api:app` | `/api/health`, `/api/presets` y `/` responden 200 |
| Contrato resultado → manifiesto → PNG/FITS | Verificado con un resultado **sintético** |
| Consulta real a IRSA SIA/TAP | **Bloqueada por el entorno**: HTTP 502 y DNS intermitente |
| FITS real descargado e inspeccionado en esta copia | **No** |

El hito **H1 (dato real actual) sigue abierto**. Las páginas estáticas de IRSA
responden 200, pero `https://irsa.ipac.caltech.edu/SIA` y `/TAP/sync` devolvieron
`502 Proxy Error` («Error reading from remote server») y el DNS falló de forma
intermitente. Por tanto, no se ha descargado ningún recorte real de SPHEREx en
esta copia y no se afirma cobertura, detección ni calidad de los cinco objetos.

Para que el equipo pueda probar la interfaz mientras IRSA se recupera, el script
`scripts/make_demo_result.py` genera un resultado **sintético claramente
etiquetado**. No son datos de SPHEREx.

## Requisitos

- Python 3.12
- Node.js 20+ (probado con Node 26.13.0 y npm 11.20.0)
- Acceso a Internet solo para consultar IRSA; las pruebas no usan red

Versiones fijadas en `requirements.txt`: FastAPI 0.115.6, uvicorn 0.34.0,
httpx 0.28.1, Astropy 7.0.0, NumPy 2.2.1, reproject 0.14.0 y Pillow 11.1.0.

## Instalación

Desde `orbitlens-spherex-ofi/`, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm --prefix frontend install
npm --prefix frontend run build
```

## Ejecución

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
```

Abrir `http://127.0.0.1:8000/`. Un solo worker es obligatorio: la cola, la
deduplicación y la caché en memoria no se comparten entre procesos.

### Desarrollo del frontend

```powershell
npm --prefix frontend run dev
```

Vite sirve en `http://127.0.0.1:5173` y redirige `/api` a `127.0.0.1:8000`.

### Configuración

Copiar `.env.example` como referencia. Las variables `ORBITLENS_*` se leen al
arrancar (por ejemplo `ORBITLENS_DATA_DIR`, `ORBITLENS_COLLECTIONS`,
`ORBITLENS_MAX_WORKERS`, `ORBITLENS_RETRY_ATTEMPTS`). No se versiona ningún
secreto ni descarga.

## Pruebas

```powershell
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
npm --prefix frontend run build
```

Las pruebas cubren coordenadas decimales y sexagesimales, parser VOTable,
máscaras por bits, FITS/WCS/reproyección, manifiestos, cola de trabajos y
contratos HTTP. **No requieren red ni datos reales.**

## Resultado sintético para probar la UI

```powershell
.\.venv\Scripts\python.exe scripts\make_demo_result.py
```

Imprime un enlace `/?result=<id>`. Ese resultado contiene 8 frames de
demostración, PNG y FITS derivados con SHA-256, y avisos que la interfaz muestra.
Sirve únicamente para validar el reproductor y el contrato de archivos.

## Verificación real contra IRSA

```powershell
.\.venv\Scripts\python.exe scripts\verify_real_data.py --target barnard --maxrec 5
.\.venv\Scripts\python.exe scripts\verify_real_data.py --target barnard --download
```

El script registra fallos en lugar de simular éxito. Sin `--download` solo
consulta SIA; con `--download` intenta un recorte, inspecciona el FITS y genera
un PNG. Si IRSA responde 502, el script termina con error y un aviso explícito.

## API

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/health` | Estado, versión y colecciones configuradas |
| `GET` | `/api/presets` | Los cinco objetivos de prueba |
| `POST` | `/api/search` | Encola una búsqueda; devuelve `job_id` (202) |
| `GET` | `/api/status/{job_id}` | Estado, fase, contadores, avisos y `result_id` |
| `GET` | `/api/results/{result_id}/manifest` | Manifiesto validado |
| `GET` | `/api/results/{result_id}/files/{file_id}` | PNG o FITS indexado |

Entradas de `/api/search`: `target_name` **o** (`ra_deg` y `dec_deg`), más
`sexagesimal`, `fov_arcmin` (1–30), `frames` (3–16) y `detector` (`auto` o
`D1`–`D6`). Los estados terminales son `ready`, `partial`, `empty` y `error`.
Un `empty` significa «sin frames utilizables», no «el objeto no existe».

## Datos, caché y límites

- Colecciones: `spherex_dr1`, `spherex_qr3`, `spherex_dr1_deep`,
  `spherex_qr3_deep`. **No se usa QR2 como fallback.**
- Solo se descargan recortes (`?center=…&size=…`), nunca FITS completos.
- Caché en disco bajo `data/`; los resultados se identifican por sus parámetros
  y por la versión del pipeline.
- Presupuesto por descarga y por trabajo, reintentos con backoff y validación de
  que el contenido descargado sea realmente FITS.
- El manifiesto se escribe de forma atómica, se valida y cada archivo se indexa
  con SHA-256 y tamaño.
- Los presets usan coordenadas J2000 aproximadas y están marcados
  `verified=False`; deben revisarse antes de afirmar identificación.

## Documentación

- [Plan funcional e historial](PLAN.md)
- [Protocolo de construcción](PROTOCOLO_CONSTRUCCION.md)
- [Fuentes del reto y decisiones](RECURSOS_RETO.md)
- [Reparto y secuencia de trabajo](TRABAJO_EQUIPO.md)
- [Entrega técnica y evidencia de ejecución](ENTREGA_TECNICA.md)
- [Decisiones científicas y límites](SCIENCE.md)

## Organización

| Integrante | Responsabilidad |
| --- | --- |
| Jesús | Ingeniería, correcciones e integración |
| Jordi | Datos y revisión científica |
| Dany | Experiencia de usuario y QA funcional |
| Terán | Demo y video |
| Regalado | Documentación, pitch y submission |

## Nota histórica

El historial de `PLAN.md` describe ejecuciones de otra copia (QR2 y un
despliegue en Render) que **no acreditan este repositorio**. Esta copia se
reconstruyó desde el protocolo y su estado se registra en
[ENTREGA_TECNICA.md](ENTREGA_TECNICA.md). La demo citada en el plan
(https://orbitlens-spherex.onrender.com) no se comprobó en esta revisión.
