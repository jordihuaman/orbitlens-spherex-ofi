# Evidencia de QA de navegador

Capturas del producto local con **datos sintéticos**, no imágenes NASA.
Reporte y alcance: [QA_EQUIPO.md](../../QA_EQUIPO.md).

Ejecutado con Playwright/Edge headless: **34 casos, 0 fallos**, escritorio
(1366×900) y viewport móvil emulado (390×844). `playwright-results.json` es la
salida generada de esa ejecución, incluyendo versión de navegador, tamaños,
tiempos y URL local por caso. Las capturas fueron abiertas e inspeccionadas por
el agente. No se prueba con ellas un dispositivo físico, producción ni cobertura
científica real.

## Rediseño de interfaz (2026-11-14)

- `ui-desktop-redesign.png` — vista completa de escritorio.
- `ui-mobile-redesign.png` — vista completa a 390 px.

SHA-256:

```text
ui-desktop-redesign.png: 24ebd811bc64bb6b1d51c9d38b236d4835e583c98b89984a3976663cf7db326b
ui-mobile-redesign.png:  bd45e536ea0a8eb70d1076f69ef486bbbb63cb25b218b51eb8c79036aabccce2
```

Las capturas anteriores (`desktop-synthetic.png`, `mobile-viewport-synthetic.png`)
se conservan como historial de la interfaz previa al rediseño.

Los reportes completos temporales, traces y descargas de cada nueva ejecución
se guardan en `frontend/test-results/` y están ignorados. Estos archivos son una
instantánea seleccionada, no un directorio que deba sobrescribirse al arrancar.
