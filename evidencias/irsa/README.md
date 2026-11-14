# Evidencia del primer recorte real DR1

- `manifest.json`: copia del manifiesto generado con código `a0ed4`, pipeline
  0.1.3, SHA-256 del original y derivados, inspección de HDU/FLAGS y tiempos FITS.
- `real-dr1-browser.png`: captura de Edge 157.0.4341.46, 1366×900, zona
  `America/Lima`; el visor muestra 29 abr 2025, 0:24 UTC.
- Se verificó la descarga del original por HTTP: 200, 3 954 240 bytes, SHA-256
  `c320ddcdb677ed23168a6cf161272c508b0dd9c808c664cdc492608014570f58`.

Los FITS no están en esta carpeta: se conservan localmente bajo
`data/results/9362cdf8afb5c043/`. Esta es evidencia, no un paquete completo de
datos. Para recuperar el recorte de la URL oficial y reconstruir los archivos,
ejecutar `scripts/download_reference_cutout.py` (requiere red salvo caché local).

Campo del tutorial Intro, no uno de los cinco objetivos. Procedencia, comandos,
lecturas y límites: [DATOS_REALES.md](../../DATOS_REALES.md).
