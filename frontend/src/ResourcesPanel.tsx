import type { Grid, Preset } from "./types";
import type { FormValues } from "./SearchForm";

const links = [
  ["SPHEREx Data Explorer — NASA/IPAC IRSA", "https://irsa.ipac.caltech.edu/applications/spherex"],
  ["Misión SPHEREx y releases DR1/QR3", "https://irsa.ipac.caltech.edu/Missions/spherex.html"],
  ["Tutoriales SPHEREx — Caltech/IPAC", "https://caltech-ipac.github.io/irsa-tutorials/spherex/"],
  ["FITS, máscaras y WCS", "https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/"],
  ["Recortes espectrales", "https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/"],
  ["Modelos de PSF", "https://caltech-ipac.github.io/irsa-tutorials/spherex-psf/"],
  ["Source Discovery Tool", "https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo/"],
  ["Mosaicos espectrales", "https://caltech-ipac.github.io/irsa-tutorials/spherex-mosaic/"],
  ["HiPS All-Sky Cube", "https://caltech-ipac.github.io/irsa-tutorials/spherex-hipscube/"],
  ["Gaia — ESA, acceso MAST", "https://archive.stsci.edu/missions-and-data/gaia"],
  ["NEOSSat — Agencia Espacial Canadiense", "https://www.asc-csa.gc.ca/eng/satellites/neossat/"],
  ["Canadian Astronomy Data Centre", "https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/"],
  ["Tutorial NEOSSat", "https://github.com/asc-csa/NEOSSAT_Tutorial"],
  ["Dataset NEOSSat (acceso externo)", "https://data.asc-csa.gc.ca/dataset/neossat"],
  ["Todos los recursos del reto", "https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/?tab=resources"],
];

function wiseView(ra: number, dec: number, fov: number): string {
  const params = new URLSearchParams({ ra: String(ra), dec: String(dec),
    size: String(fov * 60), band: "2", speed: "500", diff: "0", shift: "0",
    synth_a: "0", synth_b: "0" });
  return `http://byw.tools/wiseview#${params}`;
}

export default function ResourcesPanel({ values, presets, grid }: {
  values: FormValues; presets: Preset[]; grid?: Grid;
}) {
  const preset = presets.find((item) => item.id === values.presetId);
  const ra = grid?.ra_deg ?? preset?.ra_deg ??
    (!values.sexagesimal && values.ra.trim() ? Number(values.ra) : NaN);
  const dec = grid?.dec_deg ?? preset?.dec_deg ??
    (!values.sexagesimal && values.dec.trim() ? Number(values.dec) : NaN);
  const valid = Number.isFinite(ra) && Number.isFinite(dec) && ra >= 0 && ra < 360 && dec >= -90 && dec <= 90;

  return (
    <aside
      className="panel resources"
      id="recursos"
      aria-labelledby="resources-heading"
    >
      <p className="eyebrow">03 · Datos, métodos y contexto</p>
      <h2 id="resources-heading">Explorar recursos del reto</h2>
      <p>
        SPHEREx y WISE son misiones NASA. WiseView es operado por AMNH;
        Gaia es de ESA y NEOSSat es canadiense. Estos enlaces abren herramientas
        externas: no mezclan sus píxeles con nuestra secuencia.
      </p>

      <div className="resource-card">
        <p className="resource-label">Inspección externa del mismo campo</p>
        {valid ? (
          <>
            <a
              className="resource-action"
              href={wiseView(ra, dec, grid?.fov_arcmin ?? values.fovArcmin)}
              target="_blank"
              rel="noreferrer noopener"
            >
              Abrir este campo en WiseView (W2)
            </a>
            <p className="hint">
              {grid ? "Centro del resultado cargado" : "Referencia del formulario"}:
              RA {ra.toFixed(6)}°, Dec {dec.toFixed(6)}°. FOV convertido de arcmin
              a arcsec. No se propaga movimiento propio.
            </p>
          </>
        ) : (
          <p className="hint">
            Introduce grados decimales válidos, selecciona un preset o carga un
            resultado para enlazar el campo.
          </p>
        )}
        <a
          className="resource-link"
          href="http://byw.tools/wiseview#ra=133.786245&dec=-7.244372&size=176&band=2&speed=500&minbright=-5.1403&maxbright=500&window=0.5&diff=0&shift=0&synth_a=0&synth_b=0"
          target="_blank"
          rel="noreferrer noopener"
        >
          Ejemplo WISE 0855 facilitado (W2, 176″)
        </a>
        <p className="hint">
          Coordenadas del enlace de referencia, no una nueva identificación ni
          un preset astrométrico.
        </p>
      </div>

      <details className="resource-list">
        <summary>Archivos, herramientas y seis tutoriales SPHEREx</summary>
        <ul>
          {links.map(([name, url]) => (
            <li key={url}>
              <a href={url} target="_blank" rel="noreferrer noopener">
                {name}
              </a>
            </li>
          ))}
        </ul>
      </details>

      <p className="hint">
        Los cubos contienen canales espectrales, no una película de fechas. Un
        cambio entre imágenes puede deberse a λ, PSF, fondo o máscaras; no
        confirma movimiento.
      </p>
    </aside>
  );
}
