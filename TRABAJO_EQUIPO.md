# Reparto de trabajo — OrbitLens SPHEREx

## Objetivo y equipo

**Actualización de integración:** Jesús pidió asumir también las partes de los
demás frentes. El agente preparó QA reproducible, guion, créditos y borrador de
submission sin atribuirlos a compañeros ausentes. Material disponible:
[QA_EQUIPO.md](QA_EQUIPO.md), [GUION_DEMO.md](GUION_DEMO.md),
[CREDITOS.md](CREDITOS.md) y [SUBMISSION.md](SUBMISSION.md).
QA asistido: 28 casos Edge, escritorio y viewport móvil; no teléfono físico.
Siguen abiertos datos reales de los cinco campos, revisión científica externa,
grabación/tres ensayos, despliegue público, licencia y envío autorizado.
El diagnóstico inicial de abajo se conserva como historial, no describe la
ausencia de código en el estado actual.

**Continuación (2026-11-14):** el estado real, los comandos de arranque, las
pruebas, las opciones de hosting gratuito y los pendientes están en
[HANDOFF.md](HANDOFF.md). Ese documento es la entrada recomendada para otra
persona; este reparto conserva el contexto histórico y las responsabilidades.

Entregar una demo reproducible para explorar imágenes infrarrojas de SPHEREx,
con procedencia de datos, controles de calidad y una presentación verificable.
El alcance funcional y el historial están en [PLAN.md](PLAN.md).

Construcción: [PROTOCOLO_CONSTRUCCION.md](PROTOCOLO_CONSTRUCCION.md).
Fuentes verificadas y cambios DR1/QR3: [RECURSOS_RETO.md](RECURSOS_RETO.md).

Reparto establecido para cinco integrantes: Jesús, Jordi, Dany, Terán y Regalado.
El plan indica que los cuatro compañeros no tienen experiencia técnica: sus
entregables se pueden realizar con navegador y documentos. Jesús implementa las
correcciones de código que resulten de su revisión.

## Diagnóstico — 14 de noviembre de 2026

- Repositorio: https://github.com/jordihuaman/orbitlens-spherex-ofi
- En la inspección inicial, la única rama remota era `master`; después se publicó
  `jesus/preparacion-equipo` con documentación. Ambas siguen sin código de la aplicación.
- El commit inspeccionado de `master` es `7dfa8095f1b64d57010c6309999632a274ba8c58` (`primer commit`).
- `git ls-tree -r --name-only origin/master` muestra únicamente `PLAN.md`.
- No hay sparse checkout habilitado ni instrucciones `AGENTS.md` en el directorio examinado.
- El plan describe un MVP React/Vite/TypeScript + FastAPI/Python y pruebas previas,
  pero el código, dependencias, pruebas y artefactos no están en este repositorio.
  Las cifras del plan son antecedentes documentados, no verificaciones de esta sesión.
- `ENTREGA.md`, citado como documento del reparto previo, tampoco está disponible.

## Primer bloqueo: recuperar la implementación existente

Confirmar con el equipo dónde están el código y `ENTREGA.md`: otro repositorio,
una copia local o cambios aún sin publicar. Incorporarlos conservando su historial
cuando esté disponible. Después, revisar sus instrucciones y ejecutar los comandos
de instalación, compilación y pruebas que realmente incluya el proyecto.

## Cinco frentes de trabajo

| Responsable | Frente | Entregable principal | Rama sugerida |
| --- | --- | --- | --- |
| Jesús | Ingeniería e integración | Aplicación reproducible y versión candidata | `jesus/integracion` |
| Jordi | Datos y revisión científica | `REVISION_DATOS.md` | `jordi/datos` |
| Dany | Experiencia de usuario y QA funcional | `QA_EQUIPO.md` | `dany/qa` |
| Terán | Demo y producción audiovisual | `GUION_DEMO.md` y enlace al video | `teran/demo` |
| Regalado | Documentación, pitch y entrega | `SUBMISSION.md` | `regalado/entrega` |

### 1. Jesús — Ingeniería e integración

**Responsabilidad:** recuperar el proyecto, mantener la coherencia entre API,
pipeline y frontend, y publicar una versión que pueda reproducirse.

- [x] Inspeccionar carpeta, estado Git, ramas y contenido remoto.
- [x] Documentar el reparto y el bloqueo de código ausente.
- [ ] Localizar e incorporar el código existente y sus instrucciones.
- [ ] Aplicar H0–H4 del protocolo: DR1/QR3, lectores FITS, contratos, pruebas y despliegue.
- [ ] Reproducir instalación, pruebas Python, pruebas frontend y build disponibles.
- [ ] Revisar el recorrido búsqueda → cola → resultado → visualización.
- [ ] Corregir los fallos priorizados de Jordi y Dany.
- [ ] Comprobar caché, límites y manejo de errores con el protocolo del proyecto.
- [ ] Integrar PR, desplegar y registrar commit, URL y resultados en `ENTREGA_TECNICA.md`.

**Archivos a su cargo cuando se recuperen:** `api.py`, `coordinates.py`,
`spherex_pipeline.py`, `analysis_modes.py`, `targets.py`, `frontend/`, pruebas,
dependencias y configuración de despliegue. Estos nombres proceden del plan;
hay que confirmar la estructura real antes de editar.

**Cierre:** otra persona puede seguir las instrucciones de arranque; las pruebas
existentes y el build pasan; los fallos que impiden completar la demo están
resueltos y el commit publicado queda identificado.

### 2. Jordi — Datos y revisión científica

**Responsabilidad:** revisar que la demo explique correctamente qué muestran los
datos. No requiere programar ni certificar descubrimientos.

- [x] Preparar una ficha por cada preset: Barnard, Epsilon Indi B, WISE 0855,
  RW Aurigae y R Draconis.
- [ ] Revisar los cinco campos regenerados con DR1/QR3; no reutilizar los conteos
  de cobertura/máscaras QR2 como si describieran los datos actuales.
- [ ] Anotar coordenadas y época, colección, detector, fechas, número de frames,
  origen de datos y avisos de calidad que realmente aparezcan.
- [ ] Comparar la evidencia con el plan y registrar discrepancias para Jesús.
- [ ] Revisar etiquetas de diferencias, pila, curva central y vista Gaia/WISE
  cuando se incorporen; registrar como fuera de alcance los extras no incluidos.
- [ ] Entregar `REVISION_DATOS.md` con enlaces/capturas y resultados por preset.

**Criterios de revisión:** `ready` significa procesamiento completado; un centro
enmascarado no equivale a flujo cero; una curva del píxel central no equivale a
fotometría de una fuente; variaciones visuales pueden depender de banda o calidad.
La vista Aladin es contextual y no demuestra la identidad de una fuente SPHEREx.

**Cierre:** cinco fichas revisadas, cada afirmación respaldada por evidencia o
marcada como pendiente, y texto científico del guion revisado con Terán.

**Inicio — 2026-11-14:** cinco fichas preparadas en
[REVISION_DATOS.md](REVISION_DATOS.md), rama `jordi/datos`, base `d7320f5`.
La revisión de datos sigue bloqueada hasta recibir la implementación y los
paquetes DR1/QR3 identificados; preparar las fichas no acredita validación.

**Avance remoto — 2026-11-14:** Jordi leyó los cinco manifiestos públicos
históricos (QR2/QR3, pipeline 0.2.2), documentó discrepancias frente al protocolo
vigente y preparó texto científico para Terán en `REVISION_DATOS.md`. El enlace
del pie de la demo apunta a `12FOCUS21/orbitlens-spherex`, repositorio público
que Jesús debe examinar como posible origen del código. No se han validado
FITS ni paquetes DR1/QR3 y no se cierra la revisión de los cinco campos.

### 3. Dany — Experiencia de usuario y QA funcional

**Responsabilidad:** representar al visitante y producir errores reproducibles.

- [ ] Probar los cinco presets en escritorio y al menos uno en teléfono real.
- [ ] Revisar play/pausa, slider, velocidad, fecha y cambios de modo disponibles.
- [ ] Abrir enlaces compartidos en una nueva sesión y comprobar sus parámetros.
- [ ] Probar coordenadas válidas, entradas inválidas y mensajes de campos vacíos.
- [ ] Revisar máscaras, estados sin cobertura/parcial y errores cuando puedan
  reproducirse; pedir a Jesús un entorno controlado si hace falta.
- [ ] Comprobar legibilidad móvil, navegación por teclado y etiquetas de controles.
- [ ] Registrar resultados en `QA_EQUIPO.md` y volver a probar cada corrección.
- [ ] Verificar O1–O4 del plan y los estados de la sección 5 del protocolo;
  distinguir funciones básicas de extras opcionales del reto.

**Formato de cada caso:** ID, fecha, URL/commit si se conoce, dispositivo y
navegador, pasos, resultado esperado, resultado observado, evidencia y estado
(`pendiente`, `correcto`, `fallo` o `bloqueado`).

**Prioridad de fallos:** P0 = aplicación inutilizable o resultados atribuidos al
campo equivocado; P1 = recorrido principal o control esencial roto;
P2 = problema visual o de contenido que permite completar el recorrido.

**Cierre:** los casos anteriores tienen resultado registrado; no quedan P0/P1
abiertos en el recorrido de presentación. Un caso bloqueado no cuenta como aprobado.

### 4. Terán — Demo y producción audiovisual

**Responsabilidad:** convertir el producto en una demostración comprensible de
1–2 minutos. Dany apoya la grabación tras completar su QA.

- [ ] Escribir `GUION_DEMO.md`: problema, uso de datos NASA, recorrido y límites.
- [ ] Mostrar fechas en la animación; no narrar los planos de un cubo espectral
  como si fueran épocas distintas.
- [ ] Elegir con Jordi un campo cuya visualización se haya comprobado.
- [ ] Preparar un recorrido corto: abrir preset, comparar fechas, consultar
  calidad y compartir el campo.
- [ ] Grabar sobre la versión candidata de Jesús, con narración y texto legible.
- [ ] Editar, añadir subtítulos y créditos, y publicar el video accesible por enlace.
- [ ] Registrar tres ensayos: duración, fallos y ajustes realizados.

**Cierre:** video accesible sin permisos privados, coherente con la versión
entregada, revisado por Jordi y Regalado. Una grabación de respaldo debe
identificarse como grabación si se utiliza durante una presentación.

### 5. Regalado — Documentación, pitch y entrega

**Responsabilidad:** reunir los materiales y preparar la página oficial.

- [ ] Confirmar nombres, responsabilidades y datos del equipo.
- [ ] Verificar en la convocatoria oficial el reto, los campos obligatorios,
  formato del video y plazo; registrar su fuente y zona horaria.
- [ ] Redactar problema, solución, público, uso de datos y límites en `SUBMISSION.md`.
- [ ] Preparar créditos y fuentes: NASA/SPHEREx, IRSA, SIMBAD, CDS/Aladin y
  Gaia/WISE según el uso que se confirme en la aplicación.
- [ ] Usar DOI y atribuciones de `RECURSOS_RETO.md`; comprobar reglas de trabajo
  previo y registrar lo reutilizado frente a lo desarrollado durante el evento.
- [ ] Coordinar con Jesús las instrucciones del README y con los titulares la
  elección de licencia; no atribuir una licencia aún no acordada.
- [ ] Incorporar enlaces de código, demo y video; comprobar acceso sin sesión.
- [ ] Preparar el pitch y realizar la submission con la cuenta autorizada;
  registrar URL y confirmación de envío.

**Cierre:** campos oficiales completos, enlaces comprobados y evidencia de envío.
La preparación del texto por sí sola no significa que la submission esté enviada.

## Dependencias y orden de ejecución

1. **Arranque en paralelo:** Jesús recupera el código; Jordi prepara las
   cinco fichas; Dany prepara casos de QA; Terán redacta el guion; Regalado verifica la
   convocatoria. La demo pública citada en el plan puede usarse si está accesible,
   registrando su URL y fecha sin asumir que coincide con un commit local.
2. **Validación:** con una versión identificada, Jordi y Dany ejecutan sus revisiones y
   Jesús corrige. Priorizar fallos de la demo frente a funcionalidades adicionales.
3. **Versión candidata:** Jesús identifica el commit; Dany verifica las correcciones;
   Jordi revisa la narrativa científica; Terán graba; Regalado completa los enlaces y el pitch.
4. **Entrega:** tres ensayos, comprobación de enlaces y envío oficial. Después de
   un cambio que afecte la demo, repetir los casos afectados y revisar la grabación.

La comparación científica entre detectores y los espectros al vuelo siguen
pendientes en el plan; no forman parte de los criterios de cierre de este reparto.

## Coordinación en GitHub

- Una rama por tarea: `<nombre>/<tarea>`; integrar mediante PR a `master`.
- Cada integrante mantiene su entregable principal para reducir conflictos.
  Jesús integra cambios de código, README y configuración.
- Las ramas sugeridas se crean cuando comienza cada tarea; la publicación de este
  documento no implica que ya existan las cinco ramas ni sus entregables.
- Cada PR indica objetivo, archivos afectados, evidencia y pendientes.
- Los integrantes no técnicos pueden editar Markdown desde GitHub en una rama
  propia y abrir el PR desde la interfaz web.
- Al iniciar y cerrar cada bloque de trabajo, comunicar: terminado, siguiente,
  bloqueo y enlace al documento o incidencia.
- Jesús prioriza los fallos P0/P1; el autor del reporte verifica su corrección.

## Definición de entrega completada

- [ ] Código y dependencias publicados, con commit de entrega identificado.
- [ ] Instalación reproducible, pruebas y build comprobados por Jesús.
- [ ] Cinco fichas de datos y revisión científica documentadas.
- [ ] QA de escritorio/móvil documentado; sin P0/P1 abiertos en la demo.
- [ ] Video final y tres ensayos registrados.
- [ ] README, créditos y decisión de licencia completados.
- [ ] Código, demo y video accesibles para los evaluadores.
- [ ] Submission enviada y confirmación registrada por Regalado.
