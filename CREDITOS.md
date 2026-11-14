# Créditos, datos y atribuciones

OrbitLens es un proyecto de equipo para explorar SPHEREx; no es un producto
oficial de NASA ni implica aval de las entidades citadas.

## Datos y herramientas

| Recurso | Entidad | Uso en esta versión |
| --- | --- | --- |
| SPHEREx DR1/QR3, IRSA | NASA / JPL / Caltech-IPAC | Fuente prevista del pipeline; acceso real bloqueado en esta copia |
| Tutoriales SPHEREx | Caltech/IPAC IRSA | Referencia de acceso, HDU, máscaras, WCS espectral sin SIP y VERSION de PRIMARY |
| WiseView / imágenes WISE | AMNH / misión NASA WISE | Enlace externo contextual al campo; no se redistribuyen imágenes |
| Gaia DR3, acceso MAST | ESA / STScI | Recurso externo; no se ha descargado ni superpuesto un catálogo |
| NEOSSat, tutorial y dataset | Agencia Espacial Canadiense | Documentación y enlace; no se integran píxeles ni observaciones |
| CADC | National Research Council Canada | Archivo externo complementario |
| Astropy, NumPy, reproject, Pillow | Comunidades de software | Lectura/procesamiento/render FITS y WCS |
| FastAPI, Uvicorn, httpx | Comunidades de software | API, servidor y acceso HTTP |
| React, Vite, TypeScript, Playwright | Comunidades de software | Interfaz, build y QA de navegador |

Las imágenes de demostración se generan en `scripts/make_demo_result.py` con
NumPy. **No son datos SPHEREx, WISE ni NASA.**

## Reconocimiento SPHEREx (para productos reales utilizados)

Texto solicitado en la página oficial de IRSA:

> This publication makes use of data products from the Spectro-Photometer for
> the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx),
> which is a joint project of the Jet Propulsion Laboratory and the California
> Institute of Technology, and is funded by the National Aeronautics and Space
> Administration.

- DR1 Spectral Images: <https://www.ipac.caltech.edu/doi/10.26131/IRSA678>.
- QR3 Spectral Images: <https://www.ipac.caltech.edu/doi/10.26131/IRSA662>.

Solo citar como datos usados las releases realmente presentes en los resultados
finales. El enlace al cubo no significa que se haya analizado el cubo; el enlace
a Gaia no equivale a un overlay. Véase `RECURSOS_RETO.md` para las ocho fuentes.

## Licencias y contribuciones

No se ha elegido una licencia de OrbitLens: **pendiente de decisión de los
titulares**. No se añade una licencia de terceros al proyecto por inferencia.
Conservar las licencias propias de dependencias; si se adapta código de un
tutorial, registrar el archivo, revisión, licencia y avisos correspondientes.
Los tutoriales IRSA indican BSD-3-Clause; NEOSSAT Tutorial tiene sus propios
términos. Consultar los originales antes de copiar/distribuir material.

El reparto de Jesús, Jordi, Dany, Terán y Regalado es organizativo, no prueba
de autoría ni de trabajo realizado. Los documentos y automatizaciones de este
bloque fueron preparados con asistencia de IA a petición de Jesús. Verificar
las reglas de declaración de herramientas y trabajo previo del evento, y
confirmar nombres/contribuciones antes de enviar la submission.
