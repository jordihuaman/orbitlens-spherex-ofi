# Handoff — cómo continuar OrbitLens

Este documento resume el estado real del repositorio para que otra persona pueda
continuar sin depender de la sesión que lo construyó. No sustituye a
[README.md](README.md), [DEPLOYMENT.md](DEPLOYMENT.md) ni
[BRECHAS_REQUISITOS.md](BRECHAS_REQUISITOS.md); los complementa.

## Estado en una frase

El producto funciona y está verificado en local (backend, pipeline, UI, pruebas y
seguridad). **No hay URL pública desplegada**; la siguiente persona debe elegir
hosting, publicar y completar la aceptación. La validación científica
independiente y el video siguen pendientes.

## Último estado verificado

- Base documentada: commit `2cc96` (`feat: preparar despliegue VPS con Caddy y
  respaldos`). El commit que añade este archivo es el vigente; comprobarlo con
  `git log -1`.
- CI remoto del commit `2cc96`: **`43663971484` en verde**, trabajos
  `regression` y `security`.
- **215 pruebas Python** y **34/34 E2E** en Edge (escritorio 1366×900 y viewport
  móvil 390×844). Axe WCAG 2.0/2.1/2.2 A y AA: **0 violaciones**.
- `pip-audit`, Bandit y `npm audit`: sin hallazgos conocidos.
- No se ha probado un teléfono físico, una red externa ni producción pública.

## Qué está hecho

- Backend FastAPI + Astropy/NumPy/reproject; frontend React/Vite/TypeScript
  servido por el mismo proceso.
- Consulta SIA2 a IRSA con DR1 + QR3 y colecciones deep. **No se usa QR2 como
  fallback.**
- Recortes FITS, alineado en rejilla común, PNG, FITS derivados, manifiesto con
  SHA-256, estados `ready/partial/empty/error` y avisos de cobertura/máscaras.
- Cuotas por IP, proxy confiable, snapshots de trabajos, presupuesto temporal,
  LRU de caché, límites de descarga, SSRF sin redirects, CSP/cabeceras,
  allowlist de host, contenedor no root y solo lectura.
- Interfaz rediseñada tipo consola científica, accesible y sin recursos externos.
- Importación local explícita de secuencias y presets con centros J2026
  (`verified=False`).
- Evidencia de cinco campos reales en `evidencias/astrometria/corrected-fields/`
  y recorrido real en `evidencias/operacion/`. Los paquetes son parciales y no
  acreditan detección ni identificación astrométrica.

## Qué falta, por prioridad

### P0 — publicar y aceptar

1. Elegir hosting. Con presupuesto 0 USD:
   - **Oracle Cloud Always Free** (2 OCPU ARM + 12 GB, tarjeta solo para
     verificación) + `sslip.io` o DuckDNS. Es la opción recomendada.
   - **Azure for Students** (100 USD/12 meses, sin tarjeta) + dominio gratis del
     GitHub Student Pack. Usar `compose.free.yaml` y swap.
   - **Render Free** solo para demo: no tiene disco persistente y pierde datos.
2. Crear `.env.production` desde `.env.production.example` con el dominio real,
   contacto de seguridad y commit.
3. Ejecutar `scripts/deploy_vps.sh --check` y `scripts/deploy_vps.sh`.
   En host de 1 GB: `ORBITLENS_COMPOSE_FREE=1 ./scripts/deploy_vps.sh`.
4. Completar la lista de aceptación de [DEPLOYMENT.md](DEPLOYMENT.md):
   `/api/health`, búsqueda real, reinicio, cuotas, HTTPS/HSTS/CSP,
   `/.well-known/security.txt`, ausencia de `/docs`, `.env` y `.git`.
5. Probar desde un teléfono físico y una red externa.

### P1 — verificación

- Validación científica independiente: astrometría/épocas, λ con
  Firefly/calibraciones, máscaras y posible binariedad. No declarar detecciones.
- Escaneo externo: ZAP baseline, SSL Labs, Mozilla Observatory.
- Revisión manual de accesibilidad además de axe.
- Respaldo y restauración probados: `scripts/backup_volume.sh`.
- Monitorización/alertas y retención de logs en el host elegido.

### P2 — entrega

- Presentación y video (aplazados por el usuario).
- Revisar `SUBMISSION.md`, créditos y licencia antes de enviar.
- Registrar URL, commit, fecha y evidencia de envío.

## Arranque local en 5 minutos

Requisitos: Python 3.12, Node 22+ y Git.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
npm ci --prefix frontend
npm run build --prefix frontend
.\.venv\Scripts\python.exe scripts\serve.py
```

Abrir `http://127.0.0.1:8000`. Sin IRSA, generar la demo sintética:

```powershell
.\.venv\Scripts\python.exe scripts\make_demo_result.py
```

Abrir la URL `/?result=...` que imprime. Es una **demostración sintética**, no
SPHEREx.

## Pruebas

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
npm run build --prefix frontend
npm run test:e2e --prefix frontend
```

`npm run test:e2e` levanta el servidor QA en `127.0.0.1:8013` con datos aislados.
No requiere IRSA. Los E2E usan Edge (`msedge`); si no está, ajustar
`ORBITLENS_BROWSER_CHANNEL` o el proyecto de Playwright.

## Despliegue: lo que hay que saber

- `compose.yaml` publica el backend solo en `127.0.0.1:8000`.
- `compose.production.yaml` añade Caddy con TLS, red interna y variables que
  fallan cerrado.
- `deploy/Caddyfile` obtiene el certificado y reescribe `X-Forwarded-For`.
- `ORBITLENS_PUBLIC_ORIGIN` debe ser `https://<host>` exacto y el host debe estar
  en `ORBITLENS_ALLOWED_WEB_HOSTS`.
- `ORBITLENS_TRUSTED_PROXIES` debe ser la red concreta del proxy
  (`172.28.0.0/24` con el Compose incluido), nunca `*`.
- No ejecutar `docker compose down -v`: borra el volumen de datos.
- El backend no debe publicarse directamente ni escalarse a varios workers: la
  cola, las cuotas y los locks no se comparten entre procesos.

## Seguridad y secretos

- No hay credenciales, tokens ni claves privadas en el repositorio.
- `.env.production` está ignorado por Git. No commitearlo.
- La clave SSH usada durante la sesión de construcción era efímera y se eliminó.
  Cada operador debe generar la suya:

  ```bash
  ssh-keygen -t ed25519 -C "orbitlens-deploy"
  ```

  y añadir solo la clave **pública** al VPS.
- No compartir contraseñas por el chat ni en documentos. Usar claves SSH.
- Aplicar los controles de [SEGURIDAD.md](SEGURIDAD.md); no afirmar certificación
  ISO/SOC 2/ASVS ni pentest realizados.

## Mapa de archivos

| Archivo | Para qué |
| --- | --- |
| `api.py` | Rutas HTTP, cuotas, seguridad y ciclo de trabajos |
| `orbitlens/` | Configuración, SIA, FITS, máscaras, alineado, manifiestos |
| `frontend/src/` | UI React: `App`, `SearchForm`, `StatusPanel`, `Viewer`, `ResourcesPanel` |
| `frontend/e2e/orbitlens.spec.ts` | 34 pruebas E2E y axe |
| `tests/` | 215 pruebas Python |
| `compose.yaml` | Contenedor base |
| `compose.production.yaml` | Perfil público con Caddy |
| `compose.free.yaml` | Perfil de 900 MB para hosts gratuitos de 1 GB |
| `scripts/deploy_vps.sh` | Validación, build, arranque y healthcheck |
| `scripts/backup_volume.sh` | Respaldo del volumen con SHA-256 |
| `DEPLOYMENT.md` | Guía de despliegue y aceptación |
| `SEGURIDAD.md` | Modelo de amenazas, controles y límites |
| `BRECHAS_REQUISITOS.md` | Matriz de requisitos y pendientes |
| `QA_EQUIPO.md` | QA, capturas y conteos |
| `evidencias/` | Evidencia seleccionada versionada |

## Reglas para no romper el trabajo

1. No reutilizar los IDs históricos de resultados ni los paquetes QR2 como si
   fueran los vigentes.
2. Mantener `verified=False` en los presets hasta completar la validación.
3. No afirmar detección, movimiento propio, cobertura total ni validación
   científica sin evidencia.
4. Conservar la separación entre demo sintética, recorte real individual,
   secuencia real e importación local.
5. Un fallo de IRSA no prueba ausencia de cobertura.
6. Si se cambia el contrato de la API o los textos accesibles, actualizar los E2E.
7. Antes de cada commit: `pytest`, `ruff`, `npm run build` y, si se tocó la UI,
   `npm run test:e2e`.

## Decisiones abiertas

- Hosting definitivo y dominio (el usuario tiene presupuesto 0 USD).
- Licencia del repositorio.
- Validación científica externa.
- Presentación, video y envío oficial.

## Contacto y propiedad

El repositorio es `jordihuaman/orbitlens-spherex-ofi`. La rama publicada es
`master`. Cualquier cambio debe ir por rama y PR, con objetivo, archivos
afectados, evidencia y pendientes, según [TRABAJO_EQUIPO.md](TRABAJO_EQUIPO.md).
