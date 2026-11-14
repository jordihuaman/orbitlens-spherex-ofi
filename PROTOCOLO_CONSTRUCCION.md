# Protocolo de construcción — OrbitLens SPHEREx

Versión documental: **1.0 — 2026-11-14**. Responsable técnico: **Jesús**.
Alcance vigente: [PLAN.md](PLAN.md). Fuentes R0–R8/T1–T14:
[RECURSOS_RETO.md](RECURSOS_RETO.md).

Este es el protocolo del equipo, basado en las fuentes consultadas. Los límites,
contratos y umbrales propuestos son decisiones de OrbitLens, no requisitos de NASA.
El código aún no está en esta copia: los comandos de aplicación y los contratos
de abajo deben materializarse o conciliarse con la implementación recuperada.

## 1. H0 — Recuperar y fijar una base reproducible

1. Localizar con el equipo el repositorio/copia que contiene el MVP descrito en
   el historial, sus pruebas, `SCIENCE.md`, `VALIDATION.md` y `ENTREGA.md`.
2. Incorporar el código conservando el historial disponible. Examinar instrucciones
   y cambios locales antes de reorganizar archivos. Si el equipo confirma que no
   existe una base recuperable, construir los módulos de la sección 2.
3. Registrar en `ENTREGA_TECNICA.md`: commit base, sistema, versiones Python/Node,
   comandos, fecha, salidas y fallos. Las pruebas reportadas en noviembre 6 se
   vuelven a ejecutar; no marcar este paso aprobado por leer el plan.
4. Para código recuperado, respetar sus versiones compatibles. Para una base nueva,
   partir de Python 3.12 y Node 24 LTS, comprobar compatibilidad de dependencias
   y fijar las versiones exactas usadas en local, CI y despliegue.
5. Mantener dependencias reproducibles: lockfile Python o requisitos fijados con
   transitivas, `package-lock.json` para frontend, y dependencias de desarrollo
   diferenciadas. Registrar versiones de Astropy, NumPy y reproject en los resultados.
6. Excluir `.venv/`, `node_modules/`, credenciales y caché general del control de
   versiones. Publicar únicamente fixtures pequeños y el paquete demo versionado
   que se decida distribuir, con manifiesto y sumas de comprobación.

Comprobación inicial, desde la raíz real `orbitlens-spherex-ofi/`, en PowerShell:

```powershell
git status --short --branch
git remote -v
git fetch origin
git branch -a
python --version
node --version
npm --version
```

Arranque propuesto **una vez que existan** `requirements.txt`, `frontend/package.json`,
su lockfile y `api.py` con la aplicación `app`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1
```

Instalar también las dependencias de desarrollo mediante el mecanismo real del
repositorio. Jesús reemplazará estos ejemplos por comandos comprobados en README.

**Salida H0:** código y dependencias disponibles; instalación y arranque reproducidos.

## 2. Arquitectura y propiedad de los módulos

```text
Navegador React/Vite/TypeScript
  → FastAPI: validar, consultar caché, encolar, exponer progreso
    → Resolver coordenadas / presets
    → Cliente IRSA SIA2 / cutouts IBE
    → Pipeline Astropy + NumPy + reproject + Pillow
    → Caché: originales, FITS derivados, PNG, manifiesto
  ← JSON de estado y derivados del mismo origen
```

Un servicio sirve API y `frontend/dist`. Empezar con un solo proceso worker;
se permiten tareas/hilos de trabajo acotados sin bloquear el event loop.
Cola, deduplicación y cuotas en memoria no se comparten entre procesos.

| Módulo previsto | Responsabilidad |
| --- | --- |
| `coordinates.py`, `targets.py` | Interpretación de unidades, resolución y procedencia astrométrica |
| `irsa_client.py` o cliente ya existente | SIA2, VOTable, acceso IBE, límites, caché y errores remotos |
| `spherex_pipeline.py`, `build_sequence.py` | Selección, máscaras, WCS, derivados y manifiesto |
| `api.py` | Contratos HTTP, cola, estado, caché y entrega de archivos |
| `frontend/` | Formulario, reproductor, metadatos, enlaces y mensajes |
| `analysis_modes.py` | Diferencias/pila opcionales; independiente del recorrido básico |
| `tests/` o suite existente | Regresiones científicas, API y contratos |
| `demo/`, scripts de verificación | Paquete reproducible de los cinco campos y smoke tests |

Jesús mantiene el código. Jordi revisa datos y narrativa científica, Dany verifica
la experiencia funcional, Terán produce la demo y Regalado mantiene fuentes y
entrega. Cada fallo observado se vincula a un caso y al commit que lo corrige.

## 3. H1 — Obtener y comprobar un dato real

### 3.1 Coordenadas y unidades

- Internamente: ICRS, RA/Dec en grados, tiempos MJD con escala identificada y
  longitudes de onda en micrómetros. Conservar unidades originales y conversiones.
- Entrada decimal: RA en `[0, 360)`, Dec en `[-90, 90]`; rechazar no finitos.
  En modo sexagesimal, RA en horas y Dec en grados. El formulario debe indicar
  el modo; no interpretar una RA decimal como horas de manera implícita.
- `fov_arcmin` es el **ancho completo** de la imagen cuadrada de salida, no radio.
  Su rango inicial es 1–30 arcmin. Convertir `size_deg = fov_arcmin / 60`.
- El centro de la rejilla del reproductor permanece fijo entre épocas. Registrar
  por separado posición catalogada, época de referencia y posición propagada
  cuando exista movimiento propio; no recentrar cada frame sobre la estrella
  y borrar visualmente el movimiento que se busca explorar.
- Resolver nombres con SIMBAD si se ofrece esa entrada. Si falla, mostrar el error
  y permitir coordenadas explícitas; no sustituirlas por aproximaciones silenciosas.
  Las coordenadas históricas del plan son referencias a verificar, no resultados nuevos.

### 3.2 Descubrir las imágenes actuales

Colecciones iniciales, según T1–T3:

```text
spherex_dr1
spherex_qr3
spherex_dr1_deep
spherex_qr3_deep
```

1. Registrar la lista y fecha de consulta. Permitir cambiarla por configuración
   (`ORBITLENS_COLLECTIONS`), manteniéndola dentro de la identidad de la caché.
2. Usar `https://irsa.ipac.caltech.edu/SIA`, con `COLLECTION`, `POS`,
   `RESPONSEFORMAT=VOTABLE` y `MAXREC`. Consultar cada colección y unir resultados.
3. Para una primera prueba acotada, usar la posición de un preset y `MAXREC=10`.
   Para construir secuencias, comenzar con máximo 1000 filas por consulta;
   comprobar `QUERY_STATUS`, errores y overflow. Alcanzar el máximo sin prueba
   de completitud se registra como posible truncamiento.
4. Una consulta `POS=CIRCLE RA DEC RADIO` intersecta huellas, no asegura que el
   cutout cubra todo el campo. Para un cuadrado pequeño puede usarse como búsqueda
   conservadora el semidiagonal `fov_arcmin / (60 * sqrt(2))` más margen; validar
   después cobertura con WCS, incluyendo bordes, polos y cruce de RA=0.
5. Leer VOTable con Astropy/cliente VO. Conservar `obs_id`, `obs_collection`,
   `energy_bandpassname`, `t_min`, `t_max`, `s_region`, `access_url` y metadatos
   disponibles de versión. Un HTTP 200 con error VOTable no es una búsqueda vacía.
6. Si hay truncamiento, dividir por intervalos temporales con presupuesto finito
   o usar TAP documentado. Deduplicar límites compartidos. Si se llega al
   presupuesto, indicar consulta incompleta; no presentar la muestra como exhaustiva.
7. QR2 solo puede conservarse como artefacto histórico explícito. No consultar
   colecciones QR2 como fallback de un fallo o vacío de DR1/QR3.

Ejemplo de estructura de consulta (sustituir los marcadores por valores validados):

```text
GET /SIA?COLLECTION=spherex_dr1&POS=CIRCLE+<ra_deg>+<dec_deg>+<radius_deg>&RESPONSEFORMAT=VOTABLE&MAXREC=10
Host: irsa.ipac.caltech.edu
```

### 3.3 Descargar e inspeccionar el cutout

- Partir de `access_url` on-premises de una fila seleccionada; añadir parámetros
  con un constructor de URL, conservando los existentes:
  `center=<ra_deg>,<dec_deg>deg&size=<size_deg>deg`. No añadir este protocolo a
  enlaces S3. Limitar el cliente a los orígenes/rutas de datos configurados.
- Los cutouts siguen los ejes del padre. Solicitar un margen suficiente para la
  rotación a la salida norte-arriba, medir cobertura y recortar a la rejilla final.
  Para la prueba inicial puede usarse un factor 1.5, documentado y revisable.
- Descargar en streaming a un archivo temporal con presupuesto; verificar FITS
  antes de renombrar de forma atómica. No guardar HTML de error como `.fits` válido.
- Leer por nombres de HDU, no por índices fijos: `PRIMARY`, `IMAGE`, `FLAGS`,
  `VARIANCE`, `ZODI`, `EPSF`/`PSF`, `WCS-WAVE`. Astropy debe manejar tanto
  `ImageHDU` como `CompImageHDU`; verificar formas y tipos después de descomprimir.
- Registrar `VERSION` de PRIMARY, `DETECTOR`, `OBSID`, `BUNIT`, WCS y tiempo de
  exposición. No usar `DATE` de creación/procesamiento como fecha de observación.
- Comprobar IMAGE 2D, unidades compatibles con MJy/sr, mapas auxiliares compatibles,
  coordenadas finitas y cobertura. Si se recibe un cubo, rechazarlo en este recorrido.
- Conservar el original íntegro; los FITS reproyectados son derivados con su propia
  cabecera WCS. No copiarles una tabla espectral del padre fingiendo que describe
  sin transformación la nueva rejilla.

**Salida H1:** un cutout actual abierto, inspección registrada y PNG derivada,
sin atribuir detección a la simple presencia de un archivo.

## 4. H2 — Pipeline temporal y control científico

### 4.1 Selección reproducible

Ordenar por tiempo de observación; deduplicar la misma exposición/detector incluso
si aparece en más de una consulta o versión. Elegir una versión de procesamiento
documentada por exposición, conservando las alternativas descartadas en el informe.
Usar un desempate estable por ID/URL. Seleccionar exposiciones repartidas en el
intervalo disponible; no tomar únicamente las primeras 12 filas del servidor.

Objetivo inicial: 12 frames, máximo 16. Empezar por un detector y registrar por
qué se eligió (cobertura, fechas y calidad). Recorrer candidatos alternativos con
un presupuesto inicial de 64 descargas por trabajo, sin reintentos ilimitados.
Reportar cuántos candidatos se evaluaron y por qué se rechazaron.

### 4.2 Máscaras

Leer definiciones `MSKN*`/`MSKD*` del FLAGS de cada versión y contrastarlas con
T6/T14. Documentar en `SCIENCE.md` una política versionada. Propuesta conservadora
inicial para visualización: enmascarar los bits de TRANSIENT, OVERFLOW, SUR_ERROR,
NONFUNC, DICHROIC, MISSING_DATA, HOT, COLD, PHANMISS, NONLINEAR, PERSIST, OUTLIER,
CROSSTALK, GHOST, GHOST_FPA, GHOST_EXT, STREAK, BLOOM, SNOWBALL, HALO y
SATELLITE_HALO cuando estén definidos. Revisar cobertura antes de aceptar la política.

- Mantener SOURCE y FULLSAMPLE si no concurren bits de rechazo. SOURCE puede
  excluirse al estimar el fondo, que es una operación distinta de mostrar la fuente.
- Usar operaciones de bits con enteros; no comparar únicamente números completos
  como `2097152`. Registrar bits desconocidos y enmascararlos conservadoramente
  hasta decidir su tratamiento.
- Los bits 32/33 de resultados fotométricos no son bits del mapa de imagen:
  mantener ambos tipos separados si se añade espectrofotometría.
- Excluir NaN/Inf y datos sin cobertura. Centro inválido se muestra como tal,
  no obliga a descartar todo el campo si la cobertura restante es suficiente.
- Registrar porcentaje válido y validez central. Umbral inicial de cobertura
  por frame: 70%, decisión de producto revisable con los cinco campos.

### 4.3 WCS, escala y espectro

1. Construir una rejilla celestial común norte-arriba/este-izquierda, con centro,
   tamaño y escala constantes. Partir de la escala nominal cercana a 6.15 arcsec/px
   para imágenes individuales y comprobar el valor real; sobremuestrear no crea resolución.
2. Reproyectar brillo superficial con `reproject_interp` para exploración, conservando
   el SIP celestial. Propagar cobertura/máscaras sin interpolar enteros de bits:
   excluir de forma conservadora salidas que dependan de píxeles inválidos.
3. Verificar orientación y cierre mundo→píxel→mundo en centro y esquinas.
   En fixtures sintéticos de traslación/rotación, exigir recuperación de posiciones
   dentro de 0.1 píxel como umbral de software, no como precisión astrométrica real.
4. Para λ/ancho de banda, transformar las coordenadas al píxel del cutout original;
   cargar WCS alternativo `W` con `fobj=hdul` y desactivar SIP **solo** en ese WCS.
   Mantener `WCS-WAVE` como estimación visual. Calibraciones científicas usan
   `CWAVE`/`CBAND`, respetando coordenadas del detector y orientación.
5. IMAGE contiene fondo zodiacal sin sustraer. MVP: conservarlo y declararlo.
   Una futura sustracción de ZODI/fondo crea otro producto y otra clave de caché.
6. Calcular percentiles globales sobre píxeles válidos de la secuencia y aplicar
   el mismo estiramiento asinh a todos los frames. Guardar percentiles y parámetros.
   No normalizar cada frame independientemente sin indicarlo.
7. Exportar PNG RGBA con píxeles inválidos transparentes y FITS flotantes derivados.
   Ninguna diferencia, media o medición se calcula sobre valores de PNG.

### 4.4 Compatibilidad de operaciones opcionales

El reproductor identifica detector y λ por frame, y avisa si cambian. Para
diferencias/apilado, usar grupos del mismo detector y un criterio explícito de
compatibilidad local. Propuesta exploratoria inicial para cada pareja `i,j`:

```text
abs(lambda_i - lambda_j) <= 0.25 * min(bandwidth_i, bandwidth_j)
```

El factor 0.25 es una heurística del equipo por validar, no una recomendación
de NASA. Exigir metadatos finitos y anchos positivos y comprobar **todas** las
parejas del grupo, sin encadenar vecinos incompatibles. Para una resta/mapa de
todo el campo, evaluar λ y ancho de banda por píxel; si solo se conoce el centro,
limitar el resultado a esa región o desactivar la operación espacial.

Diferencia: `A − B` solo en soporte válido común, con escala simétrica alrededor
de cero. Pila: media de valores válidos en grupos temporales de hasta siete días,
al menos dos contribuciones por píxel y mapa del número de contribuciones.
Conservar PSF/fondo/fechas y declarar limitaciones; no afirmar mejora de S/N sin medirla.

La curva del píxel central representa brillo superficial, con `null` y motivo
cuando esté enmascarado. Fotometría de una fuente requiere posición/época,
apertura o ePSF adecuada, fondo, mezcla de fuentes, ángulo sólido y propagación
de incertidumbres. La varianza reproyectada no se obtiene simplemente tratando
VARIANCE como IMAGE: los pesos se elevan al cuadrado y aparece covarianza.
Estos análisis quedan fuera del MVP y requieren validación independiente.

**Salida H2:** cinco manifiestos verificables y cinco fichas de Jordi. Incluir
campos sin cobertura o con fuente enmascarada con su resultado real.

## 5. Contrato de datos y HTTP

Contrato objetivo a reconciliar con el código recuperado antes de modificarlo.
Mantener compatibilidad mediante adaptador o versión explícita si el API existente
es distinto; actualizar frontend, esquema y pruebas en el mismo cambio.

### Solicitud normalizada

```json
{
  "ra_deg": 133.75862792,
  "dec_deg": -7.24208853,
  "fov_arcmin": 10,
  "frames": 12,
  "detector": "auto"
}
```

La posición es un ejemplo histórico del plan, no una nueva resolución de WISE 0855.
`frames`: entero 3–16; `detector`: `auto` o `D1`…`D6`. La entrada alternativa
`target_name` se resuelve antes de formar esta solicitud; rechazar combinaciones
ambiguas de nombre y coordenadas. Unidades/rangos se validan en el servidor.

| Método/ruta prevista | Comportamiento |
| --- | --- |
| `GET /api/health` | Estado del proceso y versión del código/pipeline; no consulta IRSA |
| `GET /api/presets` | Cinco presets con estado real y enlaces disponibles |
| `POST /api/search` | `202` y `{job_id, status_url}`; trabajo pesado fuera de la petición |
| `GET /api/status/{job_id}` | Estado, fase, posición en cola si aplica, contadores, avisos y URL del manifiesto al terminar |
| `GET /api/results/{result_id}/manifest` | Manifiesto validado e inmutable de un resultado |
| `GET /api/results/{result_id}/files/{file_id}` | Solo artefactos indexados del resultado; no expone rutas arbitrarias ni `data/raw` |

Estados: `queued` → `running` → `ready`, `partial`, `empty` o `error`.
Las fases `resolving`, `searching`, `downloading`, `processing` son metadatos de
`running`, no estados terminales nuevos.

- `ready`: al menos tres frames válidos y construcción completada según la
  selección declarada; puede haber menos frames que los solicitados por cobertura.
- `partial`: uno/dos frames, o resultado útil con fallos/truncamiento sin resolver.
  Permitir reproducción solo con al menos tres frames; explicar la limitación.
- `empty`: consultas completadas sin datos utilizables; indicar si fue falta de
  cobertura, selección espectral o calidad, con contadores. No significa ausencia física del objeto.
- `error`: fallo que impide obtener un resultado utilizable. Una caída de todas
  las colecciones no es `empty`; fallos parciales quedan reflejados en `partial`.
- `ready` nunca significa detección confirmada. Archivos faltantes/corruptos
  invalidan la entrada de caché y no pueden publicarse como resultado listo.

Errores de entrada: `422`; cuotas/cola llena: `429` con `Retry-After`;
ID desconocido: `404`; expirado conocido: `410`; dependencia indisponible en una
operación síncrona: `503`. Un trabajo aceptado comunica sus fallos posteriores por
el estado JSON; el frontend no debe esperar que aparezcan como HTTP 503 del POST.

### Manifiesto mínimo

| Grupo | Campos requeridos |
| --- | --- |
| Identidad | `schema_version`, `pipeline_version`, `code_commit`, `result_id`, `created_at` |
| Entrada | coordenadas/unidades, FOV, detector, frames solicitados, resolución y época si aplica |
| Consulta | colecciones, fecha UTC, parámetros, conteos, fallos, truncamiento, selección/deduplicación |
| Rejilla | WCS de salida o enlace al FITS que lo contiene, forma, escala, orientación |
| Procesamiento | máscara y versión, bits, cobertura mínima, escala global, política espectral, tratamiento de fondo |
| Frame | ID/exposición, colección/release, detector, VERSION del FITS, t_min/t_max/MJD y escala temporal, λ/ancho y método |
| Calidad | cobertura geométrica y fracción válida, centro enmascarado, motivos de rechazo/avisos |
| Archivos | URL de origen/cutout, PNG y FITS derivados, tamaño y SHA-256 de artefactos |

Usar números finitos o `null` con motivo, nunca NaN/Infinity en JSON. Validar el
esquema en backend y tipos en frontend; no depender de campos opcionales sin fallback.
Enlaces de búsqueda con coordenadas repiten parámetros pero pueden obtener datos
nuevos; un `result_id` fija una secuencia mientras se conserve su paquete.

## 6. H3/H4 — Capacidad, caché y tolerancia a fallos

Parámetros iniciales para medir y ajustar en el entorno real:

| Control | Valor inicial / política |
| --- | --- |
| Trabajos pesados simultáneos | 3 en un único proceso |
| Trabajos activos totales, en ejecución + cola | 32 |
| Cuota por IP | 2 trabajos en curso y 10 búsquedas pesadas/minuto |
| Descargas remotas simultáneas | 3 globales, compartidas por todos los trabajos |
| Timeout remoto | conexión 10 s; lectura 120 s; presupuesto total por trabajo 600 s |
| Reintentos | hasta 2 adicionales para errores transitorios; backoff 1/2 s y `Retry-After` dentro del presupuesto |
| Tamaño máximo | 100 MiB por respuesta FITS; 512 MiB descargados por trabajo, incluidos intentos fallidos |
| Caché | presupuesto blando conjunto de 2 GiB, con archivos activos y presets protegidos |
| Caché de consultas | 24 h para búsquedas correctas; 60 s para vacíos confirmados; errores no se guardan como vacíos |

El tiempo de lectura se amplía respecto al historial porque los tutoriales T6–T8
usan 120 s. Estos valores no garantizan latencias: medir duración, bytes, memoria
y aciertos de caché. Si no hay espacio suficiente, detener nuevas descargas con
error recuperable; no borrar archivos que otro trabajo esté utilizando.

- Buscar caché y trabajo equivalente antes de reservar cómputo nuevo. Mantener
  protección barata de solicitudes; el polling no consume cuota de búsqueda pesada.
- Separar caché de consultas, cutouts y resultados. La identidad de consulta
  incluye colecciones y filtros. La de cutouts incluye URL/versión del recurso y
  tamaño. La de resultado incluye inputs normalizados, selección de exposiciones,
  releases/versiones, máscara, WCS, estiramiento y política espectral.
- El índice de búsquedas caduca junto con las consultas aunque exista un resultado
  viejo. Conservar el resultado viejo por su ID para reproducibilidad; una nueva
  selección produce un nuevo ID. Registrar `ETag`/`Last-Modified` cuando existan.
- Escribir de forma atómica y validar manifiesto, tamaño y checksum al indexar
  presets. Si falla la caché, regenerar bajo bloqueo por clave o informar error.
- Aplicar LRU sin tocar constructores activos. Inventariar cachés de Astropy y
  del cliente HTTP para que no crezcan fuera del presupuesto sin contabilizarse.
- Configurar los proxies confiables del despliegue para determinar IP. Probar
  que cabeceras enviadas por un visitante no evaden las cuotas.
- Tras un reinicio, servir resultados persistidos válidos; trabajos incompletos
  deben quedar fallidos/expirados, no perpetuamente en ejecución. Permitir reintento.

## 7. Verificación por capas

### Automática, sin servicios externos

| Caso | Comprobación significativa |
| --- | --- |
| Coordenadas | conversión horas/grados, límites, signos, RA=0 y polos; rechazo de no finitos |
| SIA/VOTable | éxito, cero filas, error con HTTP 200, overflow, columnas ausentes y deduplicación |
| FITS | IMAGE 2D, FLAGS comprimido/no comprimido, fichero truncado y selección por nombre de HDU |
| Máscaras | SOURCE solo permanece; SOURCE con bit malo se excluye; no convertir máscara a señal cero |
| WCS | fuentes sintéticas con rotación/traslación conocidas; orientación y origen de píxel correctos |
| Espectro | SIP solo desactivado en WCS W; unidades; grupo con cadena de vecinos pero extremos incompatibles |
| Escala | una fuente de brillo fijo conserva el valor visual; diferencia/pila operan sobre flotantes |
| API/caché | entradas inválidas, mismo trabajo compartido, caducidad, corrupción, error remoto frente a vacío |
| Cuotas | semáforos globales, cola llena, Retry-After y lectura de resultados durante carga |
| Frontend | parseo de URL, orden temporal frente a espectral, estados terminales y limpieza del polling |

Fixtures: pequeños, con licencia/procedencia y casos sintéticos claramente
identificados. CI no debe descargar datos masivos ni depender de IRSA/SIMBAD/CDS.
Usar el runner de la implementación recuperada. Para una base nueva, definir
`pytest` en backend y un script `test` reproducible en `frontend/package.json`;
`npm run build` debe incluir comprobación TypeScript.

### Integración acotada con datos reales

Jesús ejecuta una consulta y un cutout de DR1/QR3, guarda procedencia y comprueba
un píxel/λ con el tutorial o Firefly. Después genera los cinco campos. Registrar
por campo colecciones consultadas, detector, frames, intervalo temporal, máscaras,
λ, tiempos, tamaños y fallos. Comparar metadatos con FITS, no solo con el PNG.

Jordi verifica referencias de coordenadas/época e interpretación. Dany ejecuta los
casos de [TRABAJO_EQUIPO.md](TRABAJO_EQUIPO.md), incluido al menos un móvil real.
Para geometría real, medir residuales de fuentes de referencia cuando sea posible;
no atribuir al instrumento el umbral sintético de 0.1 píxel.

### Smoke y publicación

1. Desde una instalación limpia, ejecutar pruebas backend/frontend y build.
2. Iniciar un worker; comprobar salud, presets, manifiestos y todos sus artefactos.
3. Probar diez visitas concurrentes a resultados en caché, dos búsquedas iguales
   y cola/cuotas con un proveedor de datos controlado. Esto no mide capacidad de IRSA.
4. Desplegar el mismo commit y paquete demo, incluyendo frontend compilado.
   Evitar que el arranque descargue todos los presets desde Internet.
5. Comprobar en producción los cinco enlaces, una búsqueda acotada, errores,
   cuotas desde dos conexiones y reinicio. Registrar configuración y evidencia.
6. Mantener el artefacto previo para rollback; si el smoke falla, volver al commit
   y paquete demo anteriores compatibles, sin reutilizar manifiestos incompatibles.

**Salida H4:** URL pública verificada, informe con commit y pruebas reales, sin
P0/P1 abiertos en el recorrido principal. Un resultado `empty` correcto aprueba
el manejo de vacío, pero no demuestra que la animación de imágenes funcione.

## 8. Actualización de releases y cierre H5

Al anunciarse una release nueva:

1. Revisar R1/T1–T4 y descubrir colecciones disponibles; registrar fecha y fuente.
2. Probar un FITS y comparar cabeceras, flags, unidades, VERSION y calibraciones.
3. Actualizar configuración y, si corresponde, parser/política y versión del pipeline.
4. Regenerar presets y comparar selección, cobertura y metadatos con la versión anterior.
5. Ejecutar regresiones afectadas, build y smoke; publicar nuevo paquete con checksum.
6. Conservar el paquete previo identificado y actualizar créditos/DOI.

Para la entrega: Terán graba la versión candidata y registra tres ensayos;
Regalado incorpora los enlaces de código/demo/video, créditos y licencia elegida.
Jordi revisa afirmaciones sobre movimiento/variabilidad y Dany verifica el recorrido.
Regalado comprueba las reglas vigentes de participación, uso de trabajo previo,
formatos y plazo oficial con zona horaria; documenta qué se reutilizó y qué se
construyó durante el evento. Registrar confirmación real de submission.

## 9. Primera tarea ejecutable de Jesús

Completar H0 y luego una prueba vertical de H1: **una coordenada → una consulta
actual → un cutout → inspección FITS/WCS → PNG con procedencia**. No incorporar
extras hasta comprobar este recorrido. Cada hito cerrado debe enlazar su commit,
comandos y resultados en `ENTREGA_TECNICA.md`.
