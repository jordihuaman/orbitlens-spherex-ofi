# Operación local — pipeline 0.1.5

## Recorrido HTTP real y reinicio

`live-http.json` y `live-http.png`: Edge 157, formulario real, RW Aur D1,
FOV 4′, tres frames, estado partial por overflow. Se comprobaron reproducción,
nueve artefactos HTTP 200 y recuperación del mismo trabajo/resultado al matar
el proceso de prueba, arrancar otro y abrir el ID persistido.

**Alcance exacto:** el ensayo exitoso usó metadatos SIA reales obtenidos antes
y copiados a la caché del directorio aislado `data/live-http/`. Los originales
seleccionados para D1 se descargaron del servicio IRSA durante el recorrido.
No es evidencia de una búsqueda SIA nueva exitosa en esa petición ni de
disponibilidad permanente del archivo. El estado registra `consulta ... caché`.

`live-http-irsa-timeout.json` conserva el intento anterior: HTTP 202 seguido
de error recuperable, porque DR1/QR3 agotaron timeout. No se ocultó ni se
convirtió en ausencia de cobertura. Las pruebas no interceptan las rutas ni
usan FITS sintéticos. `frontend/e2e/live-check.mjs` permite repetir explícitamente
el ensayo con red; no se ejecuta automáticamente en CI.

El proceso se ejecutó en loopback y su directorio de datos es separado. Esto
**no** acredita un host público, teléfono físico, TLS, Docker ni cuotas detrás
de un proxy real. Esos límites están en `DEPLOYMENT.md`.

## Importador sin red

`local-sequence-manifest.json`: tres originales reales antiguos de Barnard,
reimportados como secuencia local (`c7733d27c7bfbc6a`, ready de construcción).
Sirve para verificar la ruta técnica, **no para cobertura de Barnard**, porque
conserva el centro anterior. Ver `ASTROMETRIA.md` y usar los presets nuevos.
La importación local útil de R Draconis al centro nuevo está documentada en
`evidencias/astrometria/corrected-fields/`.

## Robustez sin dependencias externas

Los tests de `test_operational_limits.py`, `test_storage.py`,
`test_local_sequence.py` y `test_service_reliability.py` comprueban cuotas,
deduplicación, proxy spoofing, snapshots/reinicio, posición de cola,
Retry-After/deadline, bytes fallidos, LRU y protección de resultados. Son
fixtures controladas, no pruebas de capacidad o latencia de producción.
