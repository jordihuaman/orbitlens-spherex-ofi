# Revisión de datos — Jordi

> Evidencia real nueva registrada por el agente: un recorte DR1 del **campo de
> referencia del tutorial**, no de los cinco objetivos, fue inspeccionado y
> servido en navegador. Detalles/hashes en `DATOS_REALES.md`. Las fichas de los
> cinco objetos siguen pendientes; no se atribuye este análisis a Jordi.

> Actualización de integración por el agente a petición de Jesús: la aplicación
> ya existe (pipeline 0.1.2). Epsilon Indi B, detector, VERSION y WCS espectral
> tienen correcciones y regresiones; ver `ENTREGA_TECNICA.md`. Hay QA de
> navegador y guion en `QA_EQUIPO.md`/`GUION_DEMO.md`. **No hay nuevos FITS reales
> ni una revisión científica firmada por Jordi**. Se conserva el informe
> original de abajo, incluidas sus observaciones históricas y fichas bloqueadas.

Fecha de inicio: **2026-11-14**. Rama: `jordi/datos`.
Base documental: `d7320f5`, integrada en `master` al iniciar este trabajo.

## Estado y alcance

**Cinco fichas preparadas; validación de datos actuales bloqueada.** Esta copia
contiene documentación, pero no aplicación, manifiestos, FITS ni presets
regenerados DR1/QR3. Se consultaron mediante GET la demo pública y sus cinco
manifiestos históricos; los resultados se registran abajo sin sustituir las
fichas actuales. No se han consultado IRSA/SIMBAD en vivo ni inspeccionado FITS,
PNG o controles del navegador.

Responsabilidad: revisar procedencia, coordenadas, calidad e interpretación,
no implementar el pipeline ni certificar detecciones.

Referencias:

- [Plan vigente](PLAN.md), especialmente O4, H1/H2 y coordenadas históricas.
- [Protocolo](PROTOCOLO_CONSTRUCCION.md), secciones 3–5 y 7.
- [Reparto de Jordi](TRABAJO_EQUIPO.md#2-jordi--datos-y-revisión-científica).
- [Fuentes y documentación técnica](RECURSOS_RETO.md).

## Cómo completar la revisión

1. Jesús entrega el commit de la aplicación y los cinco paquetes actuales:
   manifiesto, metadatos de resolución (`target.json` o equivalente), FITS
   originales/derivados y PNG, con versiones y checksums.
2. Registrar por ficha la URL exacta o ruta del paquete, `result_id`, commit,
   versión del pipeline y fecha UTC de revisión. Una URL pública sin commit
   conocido se identifica como tal; no se asume que corresponde a esta copia.
3. Contrastar coordenadas y época con la resolución astrométrica, y colección,
   detector, unidades y tiempo con los FITS. Registrar fuente y unidades.
4. Comprobar las cuatro colecciones configuradas: `spherex_dr1`, `spherex_qr3`,
   `spherex_dr1_deep` y `spherex_qr3_deep`. Distinguir colecciones consultadas de
   las que aportaron frames. Anotar errores, overflow y límites de la muestra.
5. Revisar orden temporal, rejilla WCS común, escala visual global, cobertura,
   máscara central y λ/ancho de banda por frame. Una inspección visual aislada
   no acredita alineación astrométrica ni compatibilidad espectral.
6. Adjuntar evidencia por afirmación: archivo y campo/HDU, enlace reproducible
   y captura cuando aporte contexto. Guardar capturas futuras en
   `evidencias/jordi/<preset>/`, identificadas con fecha y `result_id`.
7. Registrar discrepancias con pasos reproducibles para Jesús y volver a revisar
   el resultado corregido. No cerrar una ficha porque su estado sea `ready`.

Estados de revisión: `pendiente` (no revisado), `bloqueado` (falta una dependencia),
`revisado` (contraste realizado, con resultado y límites). El estado de revisión
es distinto del estado del pipeline (`ready`, `partial`, `empty`, `error`).
Un vacío comprobado puede ser un resultado válido de revisión, no una detección
ni una prueba de ausencia física.

## Resumen de los cinco campos

Las coordenadas siguientes son **referencias históricas de PLAN.md**, ICRS en
grados, propagadas allí a época juliana 2026.5. No se han vuelto a resolver ni
validar aquí; no sustituyen al metadato de resolución de cada nuevo paquete.
El plan advierte que no incluyen paralaje anual ni propagación por exposición.

| Preset | RA de referencia (°) | Dec de referencia (°) | Estado de revisión |
| --- | --- | --- | --- |
| Barnard | 269.44615615 | +4.76964363 | bloqueado |
| Epsilon Indi B | 331.09767931 | −56.80099136 | bloqueado |
| WISE 0855 | 133.75862792 | −7.24208853 | bloqueado |
| RW Aurigae | 76.95658774 | +30.40128852 | bloqueado |
| R Draconis | 248.16722581 | +66.75502468 | bloqueado |

### 1. Barnard

- **Estado:** bloqueado; falta paquete DR1/QR3 identificado.
- **Coordenadas/época:** referencia de la tabla; resolución actual y procedencia pendientes.
- **Identidad de versión:** commit, `result_id`, versión pipeline y fecha UTC pendientes.
- **Consulta/origen:** cuatro colecciones actuales por comprobar; filas, errores,
  truncamiento, URLs IRSA y versiones FITS pendientes.
- **Secuencia:** detector, número de frames, fechas/MJD y escala temporal pendientes.
- **Calidad:** cobertura geométrica, fracción válida, centro enmascarado, bits y
  política de máscara pendientes; λ/ancho de banda y método pendientes.
- **Revisión específica:** contrastar movimiento propio y centro fijo de salida.
  No trasladar los conteos de centro enmascarado del historial QR2.
- **Evidencia:** ninguna imagen o paquete actual disponible.
- **Conclusión:** no evaluado; no hay afirmación de detección ni movimiento medido.

### 2. Epsilon Indi B

- **Estado:** bloqueado; falta paquete DR1/QR3 identificado.
- **Coordenadas/época:** referencia de la tabla; resolución actual y procedencia pendientes.
- **Identidad de versión:** commit, `result_id`, versión pipeline y fecha UTC pendientes.
- **Consulta/origen:** cuatro colecciones actuales por comprobar; filas, errores,
  truncamiento, URLs IRSA y versiones FITS pendientes.
- **Secuencia:** detector, número de frames, fechas/MJD y escala temporal pendientes.
- **Calidad:** cobertura geométrica, fracción válida, centro enmascarado, bits y
  política de máscara pendientes; λ/ancho de banda y método pendientes.
- **Revisión específica:** comprobar que el identificador resuelto corresponde al
  objeto solicitado; una fuente visible en el campo no demuestra su identidad.
- **Evidencia:** ninguna imagen o paquete actual disponible.
- **Conclusión:** no evaluado; detectabilidad e identificación pendientes.

### 3. WISE 0855

- **Estado:** bloqueado; falta paquete DR1/QR3 identificado.
- **Coordenadas/época:** referencia de la tabla; resolución actual y procedencia pendientes.
- **Identidad de versión:** commit, `result_id`, versión pipeline y fecha UTC pendientes.
- **Consulta/origen:** cuatro colecciones actuales por comprobar; filas, errores,
  truncamiento, URLs IRSA y versiones FITS pendientes.
- **Secuencia:** detector, número de frames, fechas/MJD y escala temporal pendientes.
- **Calidad:** cobertura geométrica, fracción válida, centro enmascarado, bits y
  política de máscara pendientes; λ/ancho de banda y método pendientes.
- **Revisión específica:** no usar QR2 como fallback ni inferir cobertura actual a
  partir del vacío QR3 histórico. La posición histórica del reto tiene época no
  especificada y no equivale al centro propagado a 2026.5 del plan.
- **Evidencia:** ninguna imagen o paquete actual disponible.
- **Conclusión:** no evaluado; cobertura del campo no garantiza detectabilidad.

### 4. RW Aurigae

- **Estado:** bloqueado; falta paquete DR1/QR3 identificado.
- **Coordenadas/época:** referencia de la tabla; resolución actual y procedencia pendientes.
- **Identidad de versión:** commit, `result_id`, versión pipeline y fecha UTC pendientes.
- **Consulta/origen:** cuatro colecciones actuales por comprobar; filas, errores,
  truncamiento, URLs IRSA y versiones FITS pendientes.
- **Secuencia:** detector, número de frames, fechas/MJD y escala temporal pendientes.
- **Calidad:** cobertura geométrica, fracción válida, centro enmascarado, bits y
  política de máscara pendientes; λ/ancho de banda y método pendientes.
- **Revisión específica:** antes de atribuir cambios a variabilidad, contrastar
  longitud de onda, máscara, fondo y escala global entre épocas.
- **Evidencia:** ninguna imagen o paquete actual disponible.
- **Conclusión:** no evaluado; no se afirma variabilidad medida.

### 5. R Draconis

- **Estado:** bloqueado; falta paquete DR1/QR3 identificado.
- **Coordenadas/época:** referencia de la tabla; resolución actual y procedencia pendientes.
- **Identidad de versión:** commit, `result_id`, versión pipeline y fecha UTC pendientes.
- **Consulta/origen:** cuatro colecciones actuales por comprobar; filas, errores,
  truncamiento, URLs IRSA y versiones FITS pendientes.
- **Secuencia:** detector, número de frames, fechas/MJD y escala temporal pendientes.
- **Calidad:** cobertura geométrica, fracción válida, centro enmascarado, bits y
  política de máscara pendientes; λ/ancho de banda y método pendientes.
- **Revisión específica:** no reutilizar la aproximación antigua RA=263.2°,
  Dec=+56.9°, señalada como incorrecta en el plan. Comprobar las colecciones
  profundas y declarar truncamiento; no asumir que la muestra es exhaustiva.
- **Evidencia:** ninguna imagen o paquete actual disponible.
- **Conclusión:** no evaluado; no se afirma variabilidad medida.

## Interpretación y etiquetas por revisar

Esta tabla establece criterios, **no acredita una revisión de la interfaz**.

| Elemento | Criterio científico | Situación actual |
| --- | --- | --- |
| `ready` | Procesamiento completado, no detección confirmada | Pendiente de interfaz/manifiesto |
| Centro inválido | Sin medición válida; no flujo cero | Pendiente de máscaras |
| Secuencia | Fechas de observación reales; IMAGE 2D no es un cubo temporal | Pendiente de FITS y reproductor |
| Cambio de banda | Mostrar λ/ancho y método; mismo detector no basta | Pendiente de metadatos |
| Diferencia | Exploratoria, sobre FITS y soporte válido compatible | Extra; pendiente de confirmar inclusión |
| Pila | Media válida, contribuciones y límites; no prometer mejora de S/N sin medir | Extra; pendiente de confirmar inclusión |
| Curva central | Brillo superficial del píxel, no fotometría de la fuente; máscara como `null` | Extra; pendiente de confirmar inclusión |
| Gaia/WISE/Aladin | Contexto externo, no identificación ni overlay SPHEREx por defecto | Extra; pendiente de confirmar inclusión |
| Fondo | Declarar tratamiento del zodiacal; no asumir sustracción | Pendiente del procesamiento |

Si un extra no se incluye en la versión candidata, registrarlo como
`fuera de alcance` con referencia a esa versión, no como fallo del MVP.

## Revisión remota histórica — 2026-11-14

**Resultado:** demo accesible y cinco manifiestos legibles; no cumple por ello
la migración documental a DR1/QR3. Solo se hicieron lecturas GET, sin lanzar
búsquedas, análisis ni regeneraciones en producción.

### Evidencia y límites

- [Página pública](https://orbitlens-spherex.onrender.com/): HTML recibido.
  No se ejecutó su JavaScript ni se probó la reproducción.
- [Salud](https://orbitlens-spherex.onrender.com/api/health):
  `{"status":"ok","pipeline_version":"0.2.2","cached_presets":5}`.
- [Presets](https://orbitlens-spherex.onrender.com/api/presets): cinco entradas
  con `cached=true` y `frame_count=12`; coordenadas propagadas a 2026.5
  coincidentes con la tabla histórica al redondeo mostrado.
  La procedencia declarada es SIMBAD Harvard, recuperada el 6 de noviembre,
  tras timeout de Strasbourg; no es una nueva resolución independiente.
- [OpenAPI](https://orbitlens-spherex.onrender.com/openapi.json):
  API declarada `0.3.0`. Las rutas de lectura de manifiestos están documentadas.
- Los cinco manifiestos respondieron HTTP 200, declaran `schema_version=1`,
  pipeline `0.2.2`, creación el **2026-11-06**, estado `ready` y 12 frames.
  Ninguno aporta `code_commit`: la versión desplegada no se vincula aquí a
  ningún commit de este repositorio.
- En los cinco se declara FOV de 5 arcmin, rejilla 49×49 a 6.15 arcsec/px,
  norte arriba/este izquierda, escala asinh común con percentiles 1/99 y
  ausencia de sustracción de ZODI. Son declaraciones del manifiesto, no
  propiedades comprobadas contra los FITS.
- Todas las listas tienen MJD no decreciente. El método espectral declarado
  es `WCS-WAVE visualization lookup, without SIP`; no es calibración científica.
  La escala temporal original debe contrastarse con FITS.

### Resultados declarados por campo

Los IDs enlazan al manifiesto consultado. Cobertura es el mínimo/máximo de
`frames[].quality.valid_coverage` (porcentaje, redondeado); no se confunde con
`masked_fraction` del recorte de entrada. λ es el rango de
`wavelength_at_target.central_um`, no una banda común ni el ancho de banda.
Los conteos centrales coinciden con el historial, pero se vuelven a observar
en estos manifiestos; **no describen futuros paquetes DR1/QR3**.

| Campo / manifiesto | Detector | Colecciones que aportan frames | Fechas declaradas (UTC, días extremos) | Centro inválido | Cobertura válida | λ central (µm) |
| --- | --- | --- | --- | --- | --- | --- |
| [Barnard](https://orbitlens-spherex.onrender.com/api/results/76e5f3e44ac9db0b035cc43d/manifest) | D3 | QR2, QR3 | 2025-08-15 → 2026-08-20 | 12/12 | 70.85–95.71% | 1.6504–2.3088 |
| [Epsilon Indi B](https://orbitlens-spherex.onrender.com/api/results/900a67b80fd744bca5af4d4a/manifest) | D2 | QR2, QR3 | 2025-04-24 → 2026-10-02 | 2/12 | 76.18–98.79% | 1.1070–1.6515 |
| [WISE 0855](https://orbitlens-spherex.onrender.com/api/results/8912e9ce39460d40ab5a8ea1/manifest) | D2 | QR2 | 2025-05-06 → 2026-05-14 | 0/12 | 75.89–93.09% | 1.1012–1.5897 |
| [RW Aurigae](https://orbitlens-spherex.onrender.com/api/results/ca9f5467e482348cb3659aac/manifest) | D5 | QR2, QR3 | 2025-09-08 → 2026-09-15 | 12/12 | 69.68–97.96% | 3.8149–4.3058 |
| [R Draconis](https://orbitlens-spherex.onrender.com/api/results/47356868d75d0ac3d8abcaf4/manifest) | D1 | QR2, QR2 deep, QR3 deep | 2025-06-06 → 2026-09-27 | 12/12 | 56.39–94.88% | 0.7546–1.1134 |

### Discrepancias verificables para la integración

| ID | Observación y reproducción | Acción propuesta |
| --- | --- | --- |
| JD-04 | GET de cualquier manifiesto: `collections` contiene QR2/QR3, no DR1; `parameters.min_coverage=0.5` y `quality_policy.unknown_bits_masked=false` | Regenerar con configuración actual y política versionada; no presentar esta caché como migrada |
| JD-05 | GET del manifiesto de R Dra: `queries.spherex_qr2_deep.rows=1000`, `possibly_truncated=true`, pero `status=ready` | Revisar propagación de consulta incompleta a `partial` según contrato vigente; no afirmar exhaustividad |
| JD-06 | GET del HTML: el método exige compatibilidad aproximada solo en el centro; el glosario dice que apilado «reduce ruido» | Revisar criterio espacial antes de restar/apilar todo el campo y retirar garantía de mejora de ruido sin medición |
| JD-07 | GET del HTML: declara licencia MIT y enlaza otro repositorio | Confirmar procedencia y licencia con Jesús/Regalado; no atribuir esa licencia a esta copia sin acuerdo |

JD-04/JD-05 son diferencias respecto del protocolo vigente, no pruebas de que
la implementación histórica incumpliera su propio contrato. No se asigna
prioridad de bug sin conciliar versión y alcance con Jesús.

### Posible ubicación del código para Jesús

El pie de la demo enlaza
[`12FOCUS21/orbitlens-spherex`](https://github.com/12FOCUS21/orbitlens-spherex).
La API de GitHub confirmó un repositorio público, rama predeterminada `main`
y `pushed_at=2026-11-08T19:51:10Z`. Comando de comprobación:

```powershell
gh api repos/12FOCUS21/orbitlens-spherex --jq '{url: .html_url, default_branch: .default_branch, private: .private, pushed_at: .pushed_at}'
```

Es una pista concreta para recuperar H0, **no una confirmación de que su HEAD
sea el código desplegado**. Jesús debe revisar historial, licencia e instrucciones
antes de incorporar archivos; en este trabajo no se importó código externo.

## Texto científico propuesto para Terán

Pendiente de adaptar y revisar contra su guion y la versión candidata:

> OrbitLens permite explorar observaciones infrarrojas de un mismo campo en
> distintas fechas. Antes de interpretar un cambio, hay que revisar la longitud
> de onda, la cobertura y las máscaras. Un píxel sin datos válidos no representa
> brillo cero, y una secuencia procesada no confirma la detección del objeto ni
> un descubrimiento.

Si se muestran extras:

> La diferencia y el apilado son herramientas exploratorias que requieren datos
> compatibles. La curva central describe un píxel fijo, no la fotometría de una
> estrella. Gaia y WISE aportan contexto y no identifican por sí solos una fuente
> en las imágenes SPHEREx.

No narrar «detectamos movimiento», «medimos la variabilidad» o «mejoramos la
señal/ruido» sin una validación específica. Si se usa la demo observada aquí,
identificar sus ejemplos como históricos QR2/QR3, no como resultados DR1.

## Bloqueos y observaciones para Jesús

| ID | Tipo | Evidencia actual | Acción necesaria | Estado |
| --- | --- | --- | --- | --- |
| JD-01 | Dependencia | Árbol de `d7320f5`: solo cinco documentos, sin aplicación ni datos | Incorporar base reproducible e identificar commit | Abierto |
| JD-02 | Dependencia | No hay paquetes actuales para ninguno de los cinco campos | Regenerar DR1/QR3 y entregar manifiestos, FITS y procedencia | Abierto |
| JD-03 | Precaución documental | PLAN.md conserva conteos QR2 y coordenadas históricas bajo advertencias | Mantenerlos como historial; contrastar cada dato nuevo sin reutilizar cifras | Pendiente de contraste |

Los bloqueos JD-01–JD-03 no son bugs reproducidos ni resultados aprobados.
Las discrepancias remotas JD-04–JD-07 están documentadas arriba.
Para futuros fallos registrar: preset,
versión, pasos, esperado, observado, evidencia, prioridad acordada con Jesús,
commit de corrección y resultado de la nueva revisión.

## Cierre pendiente

- [x] Preparar las cinco fichas y criterios de revisión.
- [x] Leer metadatos de los cinco ejemplos públicos históricos y registrar límites.
- [x] Preparar texto científico propuesto para Terán, sin aprobar aún su guion.
- [ ] Contrastar coordenadas/época y procedencia de los cinco paquetes actuales.
- [ ] Registrar colección, detector, fechas, frames, λ, cobertura y máscaras reales.
- [ ] Adjuntar evidencia y resolver o declarar limitaciones por ficha.
- [ ] Revisar etiquetas de la versión candidata y alcance de extras.
- [ ] Revisar con Terán el texto científico del guion.

**Siguiente paso:** Jesús confirma la ubicación del código y entrega el primer
paquete DR1/QR3 identificado para completar su ficha; Terán comparte su guion
cuando esté disponible. La revisión histórica no cierra ninguna ficha actual.
