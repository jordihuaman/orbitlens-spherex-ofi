# Contraste de requisitos y ejecución — pipeline 0.1.6

Revisión: 2026-11-14. Base: `PLAN.md` (O1–O4),
`PROTOCOLO_CONSTRUCCION.md` (§§4–7) y evidencia de esta copia.
La presentación y el video están aplazados por el usuario.

## Objetivos e hitos

| Requisito | Estado comprobado | Brecha / siguiente condición de cierre |
| --- | --- | --- |
| O1: web pública / H4 | Pendiente | Hay ejecución local, no URL pública del código actual ni prueba sin sesión en teléfono físico. |
| O2: entrada RA/Dec | Implementado y probado | API valida decimales/sexagesimales y rangos; QA de navegador controlada. No implica resolver astrometría de presets. |
| O3: secuencia real de un mismo campo / H2 | Implementado, límites explícitos | Tres frames por campo con centrado J2026: cuatro paquetes SIA partial y uno de importación local ready de construcción. Ver `ASTROMETRIA.md`; no son mediciones científicas. |
| O4: cinco campos | Revisados técnicamente y por catálogo | Los centros anteriores de Barnard/WISE 0855 no incluían sus posiciones predichas; se corrigieron y regeneraron. En los 15 frames seleccionados la posición predicha está dentro, pero muchos píxeles están enmascarados. Sin identificación/detección confirmada. |
| H0: base reproducible | Verificado local y remotamente | 215 pruebas Python, 34 E2E, Ruff, build, `pip-audit`, Bandit y `npm audit`; CI `43659372301` en verde (`regression` + `security`) sobre `017f5`. |
| Seguridad para exposición pública | Implementada y probada localmente, no certificada | CSP/cabeceras, allowlist de host, límites de cuerpo, CSRF por origen, cuotas, SSRF sin redirects, FITS acotado, rutas/symlinks, errores genéricos, logs sin IP, contenedor no root/solo lectura y auditorías de dependencias. Faltan pentest, WAF/anti-DDoS, monitorización, respaldos probados y despliegue real. Ver `SEGURIDAD.md`. |
| H1: primer dato real actual | Evidencia parcial suficiente para lector/visor | FITS DR1 original del tutorial inspeccionado y abierto en Edge; falta contrastar píxel/λ con Firefly/tutorial y revisión astrométrica de objetivos. |
| H3: recorrido web | Verificado localmente con caché real | Formulario → pipeline → tres frames → reproducción → nueve descargas 200 → reinicio → trabajo/resultado recuperados. Metadatos SIA reales en caché, recortes de IRSA; un intento anterior agotó timeout y se conserva. Ver `evidencias/operacion/`. |
| H5: presentación/video/envío | Aplazado | No bloquea este bloque de ingeniería. No se declara enviado. |

## Brechas de robustez corregidas en este bloque

| Requisito técnico | Implementación / evidencia |
| --- | --- |
| Leer respuestas reales IRSA | `to_table(use_names_over_ids=True)`: FIELD IDs `col_*` no sustituyen los nombres `obs_id`, `access_url`, etc. Regresión dedicada y parseo de respuesta real guardada con tres filas. |
| Error remoto no equivale a vacío | Rechazo de `QUERY_STATUS=ERROR` con HTTP 200 y tablas sin columnas obligatorias. Todas las colecciones fallidas producen error; búsqueda incompleta sin candidatos no se etiqueta como vacío confirmado. |
| Vacíos caducan pronto | TTL 60 s configurable (`ORBITLENS_EMPTY_CACHE_TTL_S`); respuestas con colecciones fallidas no se guardan como correctas. |
| No promover parcial a listo | Estado parcial conservado al reutilizar artefactos; fallos de colección y overflow quedan explícitos. |
| Caché caducada ante caída total | Registros previos solo como partial con fallos actuales conservados; un vacío caducado no acredita ausencia de cobertura durante una caída. |
| Artefactos íntegros | Validación de contención de ruta, tamaño y SHA-256 antes de reutilizar y servir. API rechaza corrupción; caché dañada se regenera. |
| Recuperar candidatos | Sustitutos acotados por `max_candidates`, orden temporal final y deduplicación por OBSID dentro del detector. No se cambia silenciosamente el detector. |
| Calidad tras reproyección | Umbral de fracción válida también en rejilla de salida; rechazo documentado. |
| Procedencia reproducible | Original FITS por frame, hash en identidad del resultado, URLs, unidades y bits de máscara conservados. |
| Reproducción >=3 frames | Uno/dos frames se inspeccionan; botón de reproducción deshabilitado. Prueba en escritorio y viewport móvil. |
| Cuotas y proxy | 2 trabajos nuevos activos/IP y 10/min, Retry-After, deduplicación antes de cuota. Cadena X-Forwarded-For desde la derecha solo con proxy autorizado; arranque con proxy_headers=False. |
| Tiempo y reintentos | 600 s cooperativos, timeouts acotados al restante, 429/transitorios y Retry-After dentro del presupuesto. No se interrumpe un cálculo nativo en curso. |
| Reinicio y cola | Snapshots JSON atómicos, trabajos interrumpidos pasan a error recuperable; posición en cola visible. Recorrido real de recuperación probado. |
| Disco y concurrencia | LRU de caché regenerable solo sin constructores activos, presupuesto blando 2 GiB, reserva libre y locks por clave; temporales de descarga/caché únicos; originales cacheados con checksum. Resultados/entradas protegidos. |
| Procedencia HTTP | ETag/Last-Modified se conservan si el servidor los devuelve, sin inventarlos para archivos anteriores. |
| Importación local | Varios MEF con OBSID/tiempos/detector del FITS, URLs y hashes; orden temporal y escala común sin red. R Draconis D6 reimportado explícitamente, no fallback oculto. |
| Presets recuperables | Índice persistente validado por integridad y centro actual; la UI ofrece abrir el resultado guardado e identifica el método. No anuncia sintéticos como resultados reales. |
| Exposición HTTP | CSP estricta, HSTS en producción, allowlist de `Host`, límite de 16 KiB, timeout de cuerpo, rechazo de `Content-Encoding` y delimitación ambigua, CSRF por `Origin`/`Sec-Fetch-Site`, cuotas por IP y `Retry-After`. Pruebas en `tests/test_http_security.py`. |
| SSRF y redirecciones | Solo HTTPS, host exacto, puerto 443, sin credenciales/fragmentos ni redirects automáticos; validación antes de la red. Prueba con `MockTransport` y destino de metadata. |
| FITS hostil | Límites de HDU/ejes/píxeles/bytes/heap antes de cargar arrays; rechazo de gzip completo; MEF/WCS/detector/tiempo validados. |
| Errores y logs | Mensajes públicos sin traceback/rutas/URLs; `request_id`; logs JSON sin IP, query ni cabeceras; acceso Uvicorn desactivado. |
| Cadena de suministro | Versiones fijadas, `pip-audit`, Bandit, `npm audit`, Dependabot y trabajo CI `security`. Contenedor no root, solo lectura, `cap_drop: ALL`, límites y healthcheck. |

Pruebas principales: `tests/test_irsa_client.py`, `tests/test_service_reliability.py`,
`tests/test_api.py`, `frontend/e2e/orbitlens.spec.ts`. Las fixtures sintéticas no
son evidencia científica. La adquisición real se registra separadamente.

## Trabajo pendiente priorizado

1. **Publicación:** elegir/proveer acceso al host y volumen persistente; Docker,
   Compose, Caddy/Nginx y guía listos, pero no hay Docker instalado ni hosting
   autorizado/configurado en esta máquina. TLS/proxy, WAF/anti-DDoS,
   monitorización, respaldos y teléfono físico pendientes. Antes de anunciar,
   ejecutar pentest/ZAP, SSL Labs y Observatory; ver `SEGURIDAD.md`.
2. **Validación científica:** revisar errores de catálogo/épocas y binariedad;
   contrastar λ con Firefly/calibraciones, no solo con el mismo lector. Un píxel
   válido no confirma fuente; muchas posiciones predichas están enmascaradas.
   Ampliar muestra o bandas explícitas si aporta utilidad, sin ocultar rechazos.
3. **Operación avanzada:** probar cuotas/proxy en despliegue real, estrés sostenido
   y retención de jobs. El límite temporal/disco es cooperativo/blando, no una
   reserva o cancelación forzada de proceso. Un solo propietario por directorio.
4. **Retención de resultados:** actualmente están protegidos, sin expiración
   automática. Mantener 404 para desconocidos; añadir tombstones/410 antes de
   implementar expiración. No borrar paquetes existentes sin decisión explícita.
5. **Acceso alternativo remoto:** S3 anónimo sigue sin fallback integrado; requiere
   recorte parcial correcto de MEF/WCS-WAVE, no añadir query center a un objeto S3.

No son bloqueantes del MVP oficial: espectros, diferencias/apilado y overlays
Gaia/WISE. WiseView es contexto externo, no un overlay SPHEREx. Mantener DR1,
QR3 y ambas colecciones deep; no introducir QR2 como fallback.

## Reproducir la adquisición

```powershell
$env:ORBITLENS_CODE_COMMIT = (git rev-parse HEAD) + '+working-tree'
.\.venv\Scripts\python.exe -u scripts\verify_real_sequences.py --target all --fov 4
```

Se consultan las cuatro colecciones, secuencialmente por campo, con un intento
por petición, timeouts 5/12 s, MAXREC=20 y hasta seis candidatos por campo.
Los límites son ajustables por argumentos; existe presupuesto cooperativo global
de 600 s por trabajo en ejecución (no incluye cola), no interrupción forzada.
El informe se guarda en `data/real-data/sequences-*.json` con duración, petición,
estado, fallos y `result_id`; los paquetes permanecen en `data/results/`.
Código de salida 1 si algún campo no es `ready`: no significa necesariamente
que no existan artefactos útiles. El campo del tutorial se ejecuta con
`--target reference --fov 1.2 --detector D1` y no cuenta como O4.
