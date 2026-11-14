# Revisión de datos — Jordi

Fecha de inicio: **2026-11-14**. Rama: `jordi/datos`.
Base documental: `d7320f5`, integrada en `master` al iniciar este trabajo.

## Estado y alcance

**Cinco fichas preparadas; validación de datos actuales bloqueada.** Esta copia
contiene documentación, pero no aplicación, manifiestos, FITS ni presets
regenerados DR1/QR3. No se han ejecutado consultas ni inspecciones de imágenes
en este bloque de trabajo. No se ha comprobado la demo pública histórica.

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

## Bloqueos y observaciones para Jesús

| ID | Tipo | Evidencia actual | Acción necesaria | Estado |
| --- | --- | --- | --- | --- |
| JD-01 | Dependencia | Árbol de `d7320f5`: solo cinco documentos, sin aplicación ni datos | Incorporar base reproducible e identificar commit | Abierto |
| JD-02 | Dependencia | No hay paquetes actuales para ninguno de los cinco campos | Regenerar DR1/QR3 y entregar manifiestos, FITS y procedencia | Abierto |
| JD-03 | Precaución documental | PLAN.md conserva conteos QR2 y coordenadas históricas bajo advertencias | Mantenerlos como historial; contrastar cada dato nuevo sin reutilizar cifras | Pendiente de contraste |

No se han observado fallos de la aplicación; estos registros no son bugs
reproducidos ni resultados aprobados. Para futuros fallos registrar: preset,
versión, pasos, esperado, observado, evidencia, prioridad acordada con Jesús,
commit de corrección y resultado de la nueva revisión.

## Cierre pendiente

- [x] Preparar las cinco fichas y criterios de revisión.
- [ ] Contrastar coordenadas/época y procedencia de los cinco paquetes actuales.
- [ ] Registrar colección, detector, fechas, frames, λ, cobertura y máscaras reales.
- [ ] Adjuntar evidencia y resolver o declarar limitaciones por ficha.
- [ ] Revisar etiquetas de la versión candidata y alcance de extras.
- [ ] Revisar con Terán el texto científico del guion.

**Siguiente paso:** recibir de Jesús el primer paquete actual identificado y
completar su ficha antes de generalizar la revisión a los otros cuatro campos.
