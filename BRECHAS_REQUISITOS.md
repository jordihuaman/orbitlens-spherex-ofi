# Contraste de requisitos y ejecución — pipeline 0.1.4

Revisión: 2026-11-14. Base: `PLAN.md` (O1–O4),
`PROTOCOLO_CONSTRUCCION.md` (§§4–7) y evidencia de esta copia.
La presentación y el video están aplazados por el usuario.

## Objetivos e hitos

| Requisito | Estado comprobado | Brecha / siguiente condición de cierre |
| --- | --- | --- |
| O1: web pública / H4 | Pendiente | Hay ejecución local, no URL pública del código actual ni prueba sin sesión en teléfono físico. |
| O2: entrada RA/Dec | Implementado y probado | API valida decimales/sexagesimales y rangos; QA de navegador controlada. No implica resolver astrometría de presets. |
| O3: secuencia real de un mismo campo / H2 | Implementado, datos parciales | Tres frames alineados y reproducibles en navegador para cada uno de los cinco campos; todos partial por overflow/fallos. Falta revisión astrométrica/científica e independencia de λ. |
| O4: cinco campos | Probados técnicamente, revisión pendiente | 15 originales contrastados con OBSID/detector/VERSION/tiempos SIA; cinco fichas técnicas en `evidencias/irsa/five-fields/README.md`. Presets siguen `verified=False`; no se atribuye identificación de fuentes ni revisión a compañeros. |
| H0: base reproducible | Verificado localmente | 124 pruebas Python, 30 E2E, Ruff y build correctos; CI no depende de IRSA. |
| H1: primer dato real actual | Evidencia parcial suficiente para lector/visor | FITS DR1 original del tutorial inspeccionado y abierto en Edge; falta contrastar píxel/λ con Firefly/tutorial y revisión astrométrica de objetivos. |
| H3: recorrido web | Parcial | Recorte individual real comprobado; estados/polling y dos frames probados con proveedor controlado. Falta recorrido completo de adquisición real desde formulario. |
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

Pruebas principales: `tests/test_irsa_client.py`, `tests/test_service_reliability.py`,
`tests/test_api.py`, `frontend/e2e/orbitlens.spec.ts`. Las fixtures sintéticas no
son evidencia científica. La adquisición real se registra separadamente.

## Trabajo pendiente priorizado

1. **Datos reales:** ya se ejecutó `scripts/verify_real_sequences.py` para los cinco
   campos: tres frames por campo, todos partial. Revisar astrometría/épocas y λ
   independientemente; ampliar selección si se busca mayor línea temporal o
   resolver overflow. Un fallo 503 no prueba falta de cobertura. Los tres centros
   de R Draconis están enmascarados. Evidencia en `evidencias/irsa/five-fields/`.
2. **Ruta alternativa:** construir una secuencia desde varios recortes locales;
   hoy el importador solo publica uno. S3 anónimo sigue sin fallback integrado.
3. **Límites operativos:** cuota por IP (2 activos, 10/min), proxies confiables,
   presupuesto total 600 s y `Retry-After` dentro del presupuesto; ya existen
   semáforos globales, cola y límites de bytes, pero no satisfacen todo §6.
4. **Persistencia y almacenamiento:** presupuesto conjunto 2 GiB/LRU sin borrar
   archivos activos, bloqueo por clave de publicación, `ETag`/`Last-Modified`,
   resultados expirados conocidos 410 y posición de cola. Persistir estados para
   distinguir trabajos interrumpidos de IDs desconocidos tras reinicio.
5. **Publicación:** desplegar commit concreto y repetir recorrido real, reinicio,
   concurrencia y teléfono físico. No confundir viewport emulado con dispositivo.

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
Los límites son ajustables por argumentos; **no son aún un deadline global**.
El informe se guarda en `data/real-data/sequences-*.json` con duración, petición,
estado, fallos y `result_id`; los paquetes permanecen en `data/results/`.
Código de salida 1 si algún campo no es `ready`: no significa necesariamente
que no existan artefactos útiles. El campo del tutorial se ejecuta con
`--target reference --fov 1.2 --detector D1` y no cuenta como O4.
