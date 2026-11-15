# QA del equipo — ejecución asistida, 2026-11-14

## Actualización pipeline 0.1.6

215 pruebas Python, 34/34 E2E Edge (escritorio y viewport móvil), Ruff y build
correctos. Incluye auditoría axe WCAG, CSP, allowlist de host, límites de cuerpo
y pruebas SSRF; `pip-audit`, Bandit y `npm audit` sin hallazgos. Los presets de QA
ya usan centros J2026 derivados de catálogo/PM.
Informe actual: `evidencias/operacion/playwright-results.json`.
Las diez capturas de los cinco paquetes reales vigentes y comprobación de
45 descargas están en `evidencias/astrometria/corrected-fields/`.

El recorrido real por formulario/reinicio está en `evidencias/operacion/`:
ensayo exitoso con metadatos SIA reales en caché y recortes de IRSA; se conserva
el intento previo con timeout. No se probó hosting público ni teléfono físico.
Las secciones siguientes conservan el QA histórico de pipeline 0.1.2 y no se
atribuyen a una aceptación personal de Dany.

Preparado y ejecutado por el agente a petición de Jesús. **No es una aceptación
atribuida a Dany**. Base: `97f0a` más los cambios de este bloque (pipeline 0.1.2).
El commit que incorpora este documento identifica la versión revisada.

## Entorno y resultado

- Windows, Edge headless **157.0.4341.46**, Playwright **1.65.1**.
- Servidor real FastAPI/Uvicorn en `127.0.0.1:8013`, frontend compilado.
- Escritorio **1366×900** y viewport móvil **390×844**, táctil emulado.
- **28/28 casos pasan**, sin reintentos, omitidos ni casos flaky; duración 59.7 s.
- Inicio registrado: **2026-11-14T22:24:46.923Z**.
- Zona del navegador fijada a `America/Lima`; fecha de observación comprobada en UTC.
- Dataset: `synthetic-demo`, 8 frames, directorio aislado `data/browser-qa`.
- **No se probó un teléfono físico ni la producción pública.**

Evidencia versionada:

- [Reporte JSON de Playwright](evidencias/qa/playwright-results.json), con navegador,
  viewport, URL y resultados por caso.
- [Captura escritorio](evidencias/qa/desktop-synthetic.png).
- [Captura viewport móvil](evidencias/qa/mobile-viewport-synthetic.png).

SHA-256 de capturas:

```text
desktop: 00b9083b8297c1f041f5e985fb5a27d68f7c26e7328fae883e9006aab9f2d590
mobile:  04e9656c4ad1419c40d0800a0db50793ba3f4343482a9b47e91d84b518ee4d5e
```

## Matriz (cada fila ejecutada en ambos tamaños)

| Caso | Verificación | Resultado / alcance |
| --- | --- | --- |
| QA01 | Carga, cinco presets y Tab hacia RA | Correcto |
| QA02–06 | Cada preset, coordenada esperada, nota no verificada, envío | Correcto; búsqueda/estado controlados, no cobertura real |
| QA07 | PNG real del servidor, play/pausa, slider, velocidad, anterior/siguiente | Correcto; imágenes sintéticas |
| QA07b | Compartir, portapapeles, nueva pestaña y recarga exacta | Correcto |
| QA07c | Descargas PNG y FITS derivado | Correcto |
| QA08 | Ausencia de overflow horizontal y captura completa | Correcto a 390 y 1366 px |
| QA09 | RA=400 rechazada con 422 y alerta | Correcto contra API real, sin IRSA |
| QA10 | WiseView usa RA correcta, W2 y FOV×60; enlaces oficiales | Correcto; no se asegura disponibilidad del visor externo |
| QA11 | Petición sexagesimal conserva frames/detector | Correcto; respuesta controlada |
| QA12–14 | Polling running→ready/partial/error | Correcto; estados controlados |

El HTML, JS, manifiesto, PNG y FITS se sirven realmente por HTTP. Solo
`/api/search` y `/api/status/controlled` se interceptan en los casos señalados.
La prueba de entrada inválida usa la API sin interceptar. No hay consultas IRSA
ocultas ni cinco secuencias reales simuladas como si fueran observaciones.

## Hallazgos y correcciones

- Etiqueta sintética antes escondida en avisos desplegables: ahora visible sobre
  la imagen y en su texto alternativo (evita atribuir píxeles sintéticos a NASA).
- La revisión de capturas encontró un desplazamiento horario de cinco horas:
  los ISO sin `Z` se interpretaban como hora local. El backend ahora emite UTC
  explícito y el visor admite los manifiestos antiguos como UTC. Se añadió una
  aserción de fecha/hora en ambos proyectos con zona `America/Lima`.
- Primera ejecución: 24 casos correctos y 2 fallos del **selector de prueba**
  `getByLabel("Detector")`, no un fallo de selección funcional. Se corrigió a
  `getByRole("combobox", {name:"Detector"})`; la ejecución completa posterior es
  la que se adjunta (28/28 incluyendo recursos).
- Los enlaces contextuales no se muestran con RA inválida; la conversión
  10 arcmin → 600 arcsec queda comprobada.

## Reproducir

```powershell
npm --prefix frontend ci
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

Requiere `.venv` y dependencias Python instaladas. Playwright inicia y cierra el
servidor de QA; el puerto 8013 debe estar libre. Edge debe estar instalado.
Alternativas: definir `ORBITLENS_BROWSER_CHANNEL=chrome` o `chromium`; para el
último, instalar antes el navegador con `npx playwright install chromium` desde
`frontend/`. El servidor de QA nunca debe desplegarse en producción.

## Puertas de aceptación pendientes

| Objetivo | Estado |
| --- | --- |
| O1: web pública del commit actual | Pendiente de despliegue y smoke externo |
| O2: RA/Dec | Pruebas backend y navegador; revisión humana ampliada pendiente |
| O3: secuencia real SPHEREx | Bloqueado por acceso IRSA; UI sintética comprobada |
| O4: cinco campos reales | Bloqueado; verificar presets no equivale a validar cobertura |
| Teléfono físico, lector de pantalla, contraste y tacto reales | Pendiente |
| Capacidad multiusuario y cuotas por IP | No medida aquí |

No se declara H4 cerrado ni ausencia de fallos fuera de los recorridos probados.
