# Evidencia de catálogo y corrección de campos

Lectura principal: [ASTROMETRIA.md](../../ASTROMETRIA.md).

- `simbad-probes.json`: respuestas/consulta real de CDS (404) y espejo Harvard
  (200); cinco filas, referencias y metadata de época/unidades.
- `previous-fields-audit.json`: posiciones predichas fuera de los antiguos
  recortes de Barnard y WISE 0855; los datos no deben presentarse como cobertura
  del objeto en su época sin esta advertencia.
- `corrected-fields/acquisition-report.json`: nueva adquisición SIA/IBE con
  centros J2026, MAXREC=200, hasta ocho candidatos; cuatro paquetes de tres
  frames y uno de un frame, todos partial por fallos/truncamiento.
- `corrected-fields/r-dra-local-import.json`: importación explícita de tres D6
  existentes al centro nuevo, sin consultar IRSA. No fallback oculto de bandas.
- `corrected-fields/selected-results.json`: selección de cuatro paquetes online
  y esa importación local. No representa una consulta homogénea única.
- `*-manifest.json` y `fits-verification.json`: originales/versiones/tiempos y
  checksums verificados. Los FITS/PNG de resultados siguen en `data/` ignorado.
- `selected-astrometry-audit.json`: posición predicha dentro de los 15 frames;
  estado de su píxel próximo documentado. No confirma detecciones.
- `corrected-fields/browser-verification.json` y diez capturas: cinco paquetes
  actuales en escritorio y viewport móvil de 390 px, reproducción/pausa y los
  45 artefactos con HTTP 200. No es teléfono físico.

Versiones: pipeline 0.1.5, base `afc97+working-tree`. No se cambia a posteriori
el identificador de código registrado por cada ejecución.
