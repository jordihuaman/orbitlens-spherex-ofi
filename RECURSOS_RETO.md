# Recursos del reto y revisión técnica

Consulta: **14 de noviembre de 2026**. Alcance: todos los ocho recursos enlazados
en la pestaña Resources de Planet X and SPHEREx, más las referencias técnicas
necesarias para OrbitLens. Las páginas consultadas no equivalen a notebooks
ejecutados, datos descargados ni funcionalidades implementadas.

## R0. Fuente del alcance

[Enunciado y recursos oficiales](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/?tab=resources).
El contenido se recuperó de los datos de la página dinámica, después de que la
lectura de texto inicial mostrara únicamente el aviso de enlaces externos.

El objetivo pide una web pública, entrada RA/Dec, secuencias de imágenes SPHEREx
del mismo campo y pruebas con Barnard's Star, Epsilon Indi B, WISE 0855,
RW Aurigae y R Draconis. Las ocho “Potential Considerations” son opcionales.
No exige detectar Planet X, acreditar movimiento en todos los presets ni
integrar cada archivo/recurso de la lista.

## Los ocho recursos enlazados

| ID | Recurso y entidad | Resultado de consulta | Aplicación en OrbitLens / responsable |
| --- | --- | --- | --- |
| R1 | [SPHEREx en NASA/IPAC IRSA](https://irsa.ipac.caltech.edu/Missions/spherex.html) | Leído: releases, acceso, herramientas y reconocimiento solicitado | Fuente principal; Jesús integra, Jordi revisa procedencia |
| R2 | [SPHEREx Tutorial Notebooks — Caltech/IPAC](https://caltech-ipac.github.io/irsa-tutorials/spherex/) | Índice y seis tutoriales leídos, sin ejecutarlos | Implementación de lectura FITS/WCS/cutouts; Jesús |
| R3 | [WiseView — American Museum of Natural History](http://byw.tools/wiseview) | Interfaz leída: RA/Dec, FOV en arcsec, blink, bandas W1/W2, diferencias, Gaia DR3 | Referencia de interacción; Dany/Terán. No se probó una secuencia ni es fuente de píxeles SPHEREx |
| R4 | [Gaia Mission Data — MAST/STScI, misión ESA](https://archive.stsci.edu/missions-and-data/gaia) | Leído: astrometría, movimiento propio y accesos a DR3 | Contexto opcional; Jordi verifica épocas y Jesús integra |
| R5 | [NEOSSat — Agencia Espacial Canadiense](https://www.asc-csa.gc.ca/eng/satellites/neossat/) | Leído: misión, observaciones y enlaces a datos abiertos | Contexto educativo opcional; Jordi/Regalado |
| R6 | [Canadian Astronomy Data Centre — NRC](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/) | Portal leído; ficha NEOSSat también consultada | Archivo complementario para futura comparación; Jordi |
| R7 | [NEOSSAT Tutorial — CSA](https://github.com/asc-csa/NEOSSAT_Tutorial) | README y licencia leídos: descarga, visualización y preprocesado; notebooks no ejecutados | Referencia opcional de FITS; Jesús. No sustituye calibraciones SPHEREx |
| R8 | [NEOSSat Dataset — CSA](https://data.asc-csa.gc.ca/dataset/neossat) | Error de transporte; también falló el portal alternativo enlazado por CSA | Acceso directo pendiente; usar la ficha oficial CADC como referencia, no declarar el dataset descargado |

Alternativas oficiales examinadas para R8:

- [Portal de datos enlazado por CSA](https://donnees-data.asc-csa.gc.ca/en/dataset/9ae3e718-8b6d-40b7-8aa4-858f00e84b30): error de transporte en esta sesión.
- [Ficha NEOSSat de CADC](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/neossat/):
  accesible; distingue productos RAW, CLEAN, COR y CORD, con distintos niveles
  de corrección. No se han probado búsquedas ni descargas desde CADC.

Gaia es una misión ESA; WiseView es operado por AMNH; NEOSSat/CADC son recursos
canadienses. Su inclusión en el reto no los convierte en misiones de NASA.

## Documentación técnica complementaria consultada

| ID | Fuente | Hallazgo utilizado |
| --- | --- | --- |
| T1 | [DR1 Overview](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_dr1.html) | DR1 publicado en noviembre; reprocesa QR2, complementa QR3 e incorpora All-Sky Cube |
| T2 | [Quick Releases Overview](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html) | QR2 fuera de búsquedas IRSA/VO; descarga directa disponible hasta febrero de 2027 |
| T3 | [Archive Guide: Data Access](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-access/) | Cuatro colecciones actuales de imágenes, colección de cubos separada, SIA2 y cutouts |
| T4 | [Archive Guide: Data Products](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/) | IMAGE 2D, unidades, ePSF, calibraciones CWAVE/CBAND y estructura diferente de cubos |
| T5 | [IRSA SIA v2](https://irsa.ipac.caltech.edu/ibe/sia.html) | POS en grados ICRS, TIME en MJD, MAXREC y RESPONSEFORMAT; intersección no garantiza cobertura completa |
| T6 | [Tutorial: Data Overview](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/) | HDU por nombre, FLAGS comprimido en ejemplo DR1, WCS espectral sin SIP y conservación del WCS celestial |
| T7 | [Tutorial: Spectral Image Cutouts](https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/) | Consulta TAP, preservación de VERSION, errores de descarga y cálculo de λ en coordenadas del objetivo |
| T8 | [Tutorial: ePSF](https://caltech-ipac.github.io/irsa-tutorials/spherex-psf/) | EPSF tabular en versiones ≥7.0; correspondencia entre píxel del cutout y detector; tamaño de rejilla variable |
| T9 | [Tutorial: Source Discovery Tool](https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo/) | Diferencia entre bandas para fuentes rojas, extracción y fotometría; no es detector temporal listo para copiar |
| T10 | [Tutorial: Mosaic Cube](https://caltech-ipac.github.io/irsa-tutorials/spherex-mosaic/) | Cubo x/y/λ; el tutorial indica que Mosaic Tool no tiene API; ejemplo de fotometría sin incertidumbres |
| T11 | [Tutorial: HiPS All-Sky Cube](https://caltech-ipac.github.io/irsa-tutorials/spherex-hipscube/) | 102 canales; índices 50/51 vacíos (base cero); espectro quick-look, no serie temporal |
| T12 | [SPHEREx Cutout Capabilities](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/cutout_tool.html) y [IBE Cutouts](https://irsa.ipac.caltech.edu/ibe/cutouts.html) | `center` y `size`; tamaño es ancho completo; orientación del padre, recorte en bordes y metadatos específicos |
| T13 | [Spectral Calibrations](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/spherex_spectral_calibrations.html) | Curvas de respuesta por canal; mapas de laboratorio y calibraciones del pipeline no son intercambiables |
| T14 | [Spectrophotometry Tool y bitflags](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html) | Fondo, ePSF/PSF, varianza, posición fija, mezcla de fuentes y flags; extracción del cubo distinta de fotometría |

T3/T4 muestran fecha de actualización 12 de noviembre de 2026. Algunos ejemplos
de páginas/tutoriales todavía mencionan QR2 o contienen descripciones antiguas.
La selección de releases sigue T1–T3 y el formato se comprueba en cada FITS.
No inferir el detector a partir del texto de una captura: leer `DETECTOR` y
compararlo con `energy_bandpassname`.

El [SPHEREx Explanatory Supplement](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf)
es la referencia científica citada por estas guías. Su lectura integral no se
realizó en esta sesión; consultar y registrar su versión y secciones aplicables
al cerrar una política científica, especialmente antes de ampliar a fotometría.

## Decisiones que cambian el plan

1. **Acceso:** SIA2 → MEF individual DR1/QR3 → cutout IBE. El cliente web recibe
   derivados de nuestro backend. TAP queda como alternativa documentada para
   frescura o consultas extensas; SIA puede retrasarse alrededor de un día tras
   la ingestión semanal. No automatizar endpoints privados de las herramientas GUI.
2. **Colecciones:** consultar DR1 y QR3, wide y deep. No usar QR2 como fallback
   de búsquedas actuales ni asumir que WISE 0855 continúa sin cobertura en QR3.
3. **Caché:** invalidar derivados al cambiar releases, máscaras o pipeline;
   comprobar los cinco campos nuevamente. Un manifiesto histórico no valida DR1.
4. **Producto:** imágenes individuales para tiempo; cubos/HiPS para espectro y
   contexto futuros. Los PNG HiPS tienen escala visual limitada y no son fotometría.
5. **Calidad:** decodificar bits, no descartar todo `FLAGS != 0`. SOURCE y
   FULLSAMPLE no son por sí solos fallos instrumentales. No trasladar literalmente
   selecciones numéricas simplificadas de un notebook a una política general.
6. **Comparabilidad:** detector, λ, ancho de banda, PSF, máscara y fondo importan.
   Una resta D2−D4 del tutorial de descubrimiento es una comparación de color,
   no evidencia de movimiento temporal.
7. **Datos auxiliares:** Gaia DR3/WISE y NEOSSat son extensiones; cada una conserva
   su catálogo/release, época, unidades y tratamiento. Una superposición exige
   transformar coordenadas al mismo WCS, y movimiento propio cuando corresponda.

## Créditos y citas para la entrega

Regalado incluirá las fuentes realmente utilizadas. Según las páginas de release:

| Producto usado | DOI |
| --- | --- |
| SPHEREx DR1 Spectral Images | [10.26131/IRSA678](https://www.ipac.caltech.edu/doi/10.26131/IRSA678) |
| SPHEREx QR3 Spectral Images | [10.26131/IRSA662](https://www.ipac.caltech.edu/doi/10.26131/IRSA662) |
| SPHEREx DR1 All-Sky Cube, solo si se utiliza | [10.26131/IRSA679](https://www.ipac.caltech.edu/doi/10.26131/IRSA679) |
| QR2 histórico, si se distribuye material de esa release | [10.26131/IRSA652](https://www.ipac.caltech.edu/doi/irsa/10.26131/IRSA652) |

Reconocimiento solicitado por IRSA para productos SPHEREx:

> This publication makes use of data products from the Spectro-Photometer for
> the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx),
> which is a joint project of the Jet Propulsion Laboratory and the California
> Institute of Technology, and is funded by the National Aeronautics and Space
> Administration.

Los tutoriales IRSA declaran BSD-3-Clause; conservar su licencia si se adapta
código. El [LICENSE.txt de NEOSSAT Tutorial](https://raw.githubusercontent.com/asc-csa/NEOSSAT_Tutorial/main/LICENSE.txt)
contiene MIT modificada, incluido un apartado de uso del nombre para promoción.
La licencia de OrbitLens debe acordarse por separado; no se ha elegido en esta
revisión. Registrar atribuciones de Gaia/WISE/CDS cuando se incorporen y distinguir
código consultado de código reutilizado.

## Pendientes de la revisión

### Integración práctica posterior — 2026-11-14

La pestaña **Resources se volvió a abrir en Edge real** y se comprobaron sus
ocho enlaces: IRSA, SPHEREx Tutorial Notebooks, WiseView, Gaia/MAST y cuatro
recursos CSA/CADC/NEOSSat. La extracción simple solo devolvía el aviso de enlaces
externos; no se tomó ese aviso como todo el contenido de la página.

Uso incorporado (pipeline 0.1.2):

- Panel del visor con las ocho fuentes y los seis tutoriales SPHEREx.
- Enlace al campo en WiseView W2, FOV arcmin×60→arcsec, sin diferencia,
  desplazamiento ni inyección sintética activados. No es overlay ni ingestión WISE.
- El ejemplo WISE proporcionado por el usuario se conserva como referencia
  externa, no como coordenada astrométrica revisada de un preset.
- Tutorial Intro §8b: SIP se excluye solo de la copia del WCS espectral;
  se conserva el WCS celestial. Regresión con FITS sintético.
- Tutorial Cutouts §6: `VERSION` se conserva desde PRIMARY. Se reconoce el
  `DETECTOR` numérico del FITS (1–6), además de etiquetas SIA `SPHEREx-Dn`.
- PSF, Source Discovery Tool, Mosaic y HiPS quedan accesibles como herramientas
  oficiales externas. No se finge fotometría, ePSF integrada ni cubo temporal.

Sonda adicional de datos: se intentó un **recorte de 0.02 grados** de la URL DR1
publicada en el tutorial Intro (no un archivo completo, ni uno de los cinco
objetivos). IBE devolvió **503 Service Unavailable**. No se obtuvo un FITS ni se
cerró H1. No se usaron imágenes de la página como sustituto de datos FITS.

WiseView devolvió contenido estático a la herramienta de lectura, pero abrir el
campo en Edge terminó en `ERR_CONNECTION_TIMED_OUT`; **no se verificaron sus
imágenes ni movimiento de WISE 0855**. Los tests de enlace solo acreditan URL y
conversión de unidades, no la disponibilidad externa. La web oficial del reto y
los tutoriales SPHEREx sí se leyeron en esta revisión.

`CREDITOS.md`, `QA_EQUIPO.md`, `GUION_DEMO.md` y `SUBMISSION.md` distinguen estos
usos y sus límites. La NASA lista recursos de otras instituciones: no atribuir
Gaia, NEOSSat ni la operación de WiseView a NASA.

- Acceso directo al dataset NEOSSat; no bloquea el MVP SPHEREx.
- Ejecución acotada de consultas/cutouts actuales y comprobación de sus cabeceras.
- Validación de máscaras, alineación, comparabilidad y cobertura de los cinco campos.
- Revisión de requisitos oficiales de entrega, licencia propia y evidencias de envío.

Estas tareas están integradas en [PLAN.md](PLAN.md) y
[PROTOCOLO_CONSTRUCCION.md](PROTOCOLO_CONSTRUCCION.md).
