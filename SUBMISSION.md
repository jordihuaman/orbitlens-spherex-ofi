# Submission — borrador para completar, NO enviado

Preparado para Jesús como sustitución asistida de la redacción de Regalado.
No se accedió a cuentas, no se envió un formulario y no se confirma elegibilidad.
Los siguientes campos son una propuesta editorial, no una transcripción de un
formulario oficial autenticado.

## Identificación y enlaces

- **Proyecto:** OrbitLens — SPHEREx.
- **Reto:** Planet X and SPHEREx.
- **Fuente:** <https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/>.
- **Código:** <https://github.com/jordihuaman/orbitlens-spherex-ofi>.
- **Versión:** commit que incorpora este archivo; consultar `git rev-parse HEAD`.
- **Demo pública de esta versión:** pendiente de despliegue y verificación.
- **Video final:** pendiente de grabación y publicación (`GUION_DEMO.md`).
- **Nombres completos / ciudad / miembros y aportaciones:** confirmar con los interesados.

No utilizar la URL histórica de Render como prueba de despliegue de este commit.

## Resumen propuesto (ES)

OrbitLens hace más accesible la exploración temporal de imágenes infrarrojas de
SPHEREx. A partir de RA/Dec, prepara una secuencia de un campo fijo con fechas,
detector, calidad y procedencia, y permite compartir resultados y descargar
derivados. Integra enlaces al archivo NASA/IPAC IRSA, tutoriales oficiales y
WiseView para contexto WISE separado. La interfaz se ha comprobado en navegador
con imágenes sintéticas explícitamente etiquetadas. La validación de imágenes
reales DR1/QR3 y de los cinco campos continúa bloqueada por el acceso a IRSA;
no anunciamos detecciones ni movimiento propio confirmado.

## Suggested summary (EN)

OrbitLens makes time-domain exploration of SPHEREx infrared images more
accessible. Given right ascension and declination, it prepares a fixed-field
sequence with observation dates, detector, quality and provenance, with
shareable results and downloadable derivatives. It links to NASA/IPAC IRSA,
official tutorials and WiseView for separate WISE context. Browser workflows
have been tested using explicitly labelled synthetic images. Validation with
real DR1/QR3 images and the five challenge fields remains blocked by IRSA access
failures; we do not claim detections or confirmed proper motion.

## Problema, solución y público

**Problema:** explorar observaciones de distintas épocas exige conservar
orientación, escala y metadatos; diferencias de banda/calidad pueden confundirse
con movimiento. **Solución:** consulta acotada, recortes, máscaras, rejilla común,
escala visual global y un manifiesto trazable. **Público previsto:** visitantes,
educadores y exploradores ciudadanos; no sustituye un análisis científico de
fuentes ni se ha medido adopción real de usuarios.

## Uso de los recursos oficiales

- SPHEREx DR1/QR3: fuente de datos prevista, cuatro colecciones; sin fallback QR2.
- Tutoriales IRSA: guían interpretación de FITS, WCS, máscaras y procedencia.
- WiseView: comparación externa con WISE; AMNH opera la herramienta.
- Gaia/ESA y NEOSSat/CSA/CADC: recursos complementarios accesibles por enlaces;
  no se declara integración de sus datos ni de todo lo enlazado por el reto.
- Lista, DOIs, reconocimiento y estado de uso: `CREDITOS.md` y `RECURSOS_RETO.md`.

## Evidencia y límites

| Evidencia | Qué acredita | Qué no acredita |
| --- | --- | --- |
| 100 pruebas Python + Ruff | Contratos y pipeline con fixtures | Calibración o detectabilidad reales |
| 28 casos Playwright, Edge, dos viewports | Controles y flujo web controlado | Teléfono físico, producción, cobertura real |
| Manifiesto y FITS sintéticos | Integridad/descarga y funcionamiento del visor | Datos científicos de NASA |
| Ocho enlaces oficiales reconsultados | Trazabilidad de recursos | Que todos sus datasets hayan sido descargados |

Falta validar varios frames reales de los cinco objetos, astrometría actual,
calidad, comparabilidad espectral y alineación. Diferencia, apilado, fotometría,
descubrimiento automático y overlay de catálogos no se anuncian como implementados.

## Pitch breve (aprox. 30 s; ensayar, no duración medida)

«Comparar imágenes del cielo no debería hacernos perder su contexto científico.
OrbitLens reúne un campo, sus fechas, su calidad y su procedencia en un visor
compartible. Nos apoyamos en SPHEREx de NASA y las herramientas de IRSA, y
conectamos con WiseView sin mezclar misiones. La interfaz ya está probada;
mostramos honestamente datos sintéticos mientras cerramos el acceso a los datos
reales. Nuestro objetivo es facilitar la exploración, no anunciar un hallazgo.»

## Antes del envío (no marcar por preparar el texto)

- [ ] Comprobar bases oficiales, elegibilidad, trabajo previo/IA, plazo y zona horaria.
- [ ] Abrir el formulario oficial con la cuenta autorizada y conciliar campos/límites.
- [ ] Confirmar integrantes, aportaciones, consentimiento y licencia.
- [ ] Desplegar el commit final y verificar enlace sin sesión desde otra conexión.
- [ ] Incluir video real con créditos, subtítulos y duración permitida.
- [ ] Adjuntar evidencia de los cinco campos o declarar explícitamente el bloqueo.
- [ ] Revisar narrativa científica y tres ensayos.
- [ ] Enviar con autorización y registrar URL/fecha/confirmación verificable.

**Plazo oficial y reglas de envío: no verificados aquí.** La página de Resources
no acredita ni una fecha límite ni la elegibilidad del proyecto.
