# Evidencia de QA de navegador

Capturas del producto local con **datos sintéticos**, no imágenes NASA.
Reporte y alcance: [QA_EQUIPO.md](../../QA_EQUIPO.md).

Ejecutado con Playwright/Edge headless: 28 casos, 0 fallos, escritorio y viewport
móvil emulado. `playwright-results.json` es la salida generada de esa ejecución,
incluyendo versión de navegador, tamaños, tiempos y URL local por caso.
Las capturas fueron abiertas e inspeccionadas por el agente. No se prueba
con ellas un dispositivo físico, producción ni cobertura científica real.

Los reportes completos temporales, traces y descargas de cada nueva ejecución
se guardan en `frontend/test-results/` y están ignorados. Estos tres archivos son
una instantánea seleccionada, no un directorio que deba sobrescribirse al arrancar.
