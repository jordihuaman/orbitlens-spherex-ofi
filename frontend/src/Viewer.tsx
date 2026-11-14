import { useEffect, useState } from "react";

import { fileUrl, manifestUrl } from "./api";
import type { Frame, Manifest } from "./types";

interface Props {
  manifest: Manifest;
}

const SPEEDS = [300, 600, 900, 1500];

function formatDate(frame: Frame): string {
  if (frame.time.label) {
    // Los manifiestos antiguos usan Astropy isot sin Z, pero declaran UTC.
    const label = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(frame.time.label)
      ? frame.time.label : `${frame.time.label}Z`;
    const date = new Date(label);
    if (!Number.isNaN(date.getTime())) {
      return `${date.toLocaleString("es-ES", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      })} UTC`;
    }
  }
  if (frame.time.t_min_mjd !== null) {
    return `MJD ${frame.time.t_min_mjd.toFixed(3)}`;
  }
  return "fecha no disponible";
}

function formatValue(value: number | null, unit: string): string {
  return value === null ? "no disponible" : `${value.toFixed(3)} ${unit}`;
}

export default function Viewer({ manifest }: Props) {
  const frames = manifest.frames;
  const synthetic = frames.some((frame) => frame.collection === "synthetic-demo");
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(900);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setIndex(0);
    setPlaying(false);
  }, [manifest.result_id]);

  useEffect(() => {
    if (!playing || frames.length < 3) {
      return;
    }
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % frames.length);
    }, speed);
    return () => window.clearInterval(timer);
  }, [playing, speed, frames.length]);

  useEffect(() => {
    frames.forEach((frame) => {
      const image = new Image();
      image.src = fileUrl(manifest.result_id, `${frame.frame_id}-png`);
    });
  }, [frames, manifest.result_id]);

  if (frames.length === 0) {
    return (
      <div className="panel notice">
        <h2>Manifiesto sin frames</h2>
        <p>El resultado no contiene imágenes reproducibles.</p>
      </div>
    );
  }

  const frame = frames[Math.min(index, frames.length - 1)];
  const pngFile = manifest.files.find(
    (file) => file.id === `${frame.frame_id}-png`,
  );
  const fitsFile = manifest.files.find(
    (file) => file.id === `${frame.frame_id}-fits`,
  );
  const originalFile = manifest.files.find((file) => file.id === `${frame.frame_id}-original`);

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="panel viewer">
      <div className="viewer-heading">
        <div>
          <p className="eyebrow">Resultado {manifest.result_id}</p>
          <h2>{frames.length === 1 ? "Recorte individual" : "Secuencia temporal"}</h2>
        </div>
        <button className="ghost" type="button" onClick={copyLink}>
          {copied ? "Enlace copiado" : "Compartir"}
        </button>
      </div>

      {manifest.status === "partial" && (
        <p role="note">Resultado parcial: la consulta o construcción no es exhaustiva. Revisa los avisos antes de interpretar cambios.</p>
      )}
      {manifest.search.method === "local-sequence-import" && (
        <p role="note">Secuencia importada localmente: procedencia declarada por el operador, sin nueva consulta a IRSA.</p>
      )}
      {synthetic && (
        <p className="notice" role="note">
          Demostración sintética: no son imágenes de SPHEREx ni una detección.
        </p>
      )}
      {!synthetic && frames.length === 1 && (
        <p role="note">Recorte real individual: no constituye una secuencia temporal ni confirma una detección.</p>
      )}
      {frames.length === 2 && (
        <p role="note">Solo hay dos frames: puedes inspeccionarlos, pero la reproducción requiere al menos tres.</p>
      )}

      <figure className="stage">
        <img
          src={fileUrl(manifest.result_id, `${frame.frame_id}-png`)}
          alt={`${synthetic ? "Imagen sintética" : "Imagen SPHEREx"} ${frame.obs_id}`}
        />
        <figcaption>
          <strong>{formatDate(frame)}</strong>
          <span>
            {index + 1} / {frames.length}
          </span>
        </figcaption>
      </figure>

      <div className="controls">
        <button
          type="button"
          className="ghost"
          aria-label="Frame anterior"
          onClick={() =>
            setIndex((current) => (current - 1 + frames.length) % frames.length)
          }
        >
          ‹
        </button>
        <button
          type="button"
          className="primary compact"
          onClick={() => setPlaying((current) => !current)}
          disabled={frames.length < 3}
        >
          {playing ? "Pausa" : "Reproducir"}
        </button>
        <button
          type="button"
          className="ghost"
          aria-label="Frame siguiente"
          onClick={() => setIndex((current) => (current + 1) % frames.length)}
        >
          ›
        </button>
        <input
          className="timeline"
          type="range"
          min={0}
          max={frames.length - 1}
          value={index}
          aria-label="Seleccionar frame"
          onChange={(event) => setIndex(Number(event.target.value))}
        />
        <label className="speed">
          <span>Velocidad</span>
          <select
            value={speed}
            onChange={(event) => setSpeed(Number(event.target.value))}
          >
            {SPEEDS.map((milliseconds) => (
              <option key={milliseconds} value={milliseconds}>
                {milliseconds} ms
              </option>
            ))}
          </select>
        </label>
      </div>

      <dl className="metadata">
        <div>
          <dt>Colección</dt>
          <dd>{frame.collection}</dd>
        </div>
        <div>
          <dt>Detector</dt>
          <dd>{frame.detector ?? "no disponible"}</dd>
        </div>
        <div>
          <dt>λ central</dt>
          <dd>{formatValue(frame.lambda_um, "µm")}</dd>
        </div>
        <div>
          <dt>Ancho de banda</dt>
          <dd>{formatValue(frame.bandwidth_um, "µm")}</dd>
        </div>
        <div>
          <dt>Cobertura válida</dt>
          <dd>{(frame.valid_fraction * 100).toFixed(1)}%</dd>
        </div>
        <div>
          <dt>Centro</dt>
          <dd>{frame.center_valid ? "válido" : "enmascarado"}</dd>
        </div>
        <div>
          <dt>VERSION</dt>
          <dd>{frame.version ?? "no disponible"}</dd>
        </div>
        <div>
          <dt>obs_id</dt>
          <dd className="mono">{frame.obs_id}</dd>
        </div>
      </dl>

      <div className="downloads">
        {originalFile && (
          <a href={fileUrl(manifest.result_id, originalFile.id)} download>FITS original</a>
        )}
        {pngFile && (
          <a href={fileUrl(manifest.result_id, pngFile.id)} download>
            PNG
          </a>
        )}
        {fitsFile && (
          <a href={fileUrl(manifest.result_id, fitsFile.id)} download>
            FITS derivado
          </a>
        )}
        <a
          href={manifestUrl(manifest.result_id)}
          target="_blank"
          rel="noreferrer"
        >
          Manifiesto
        </a>
      </div>

      {frame.warnings.length > 0 && (
        <details className="warnings">
          <summary>Avisos del frame ({frame.warnings.length})</summary>
          <ul>
            {frame.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </details>
      )}

      {manifest.warnings.length > 0 && (
        <details className="warnings">
          <summary>Avisos del resultado ({manifest.warnings.length})</summary>
          <ul>
            {manifest.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </details>
      )}

      <p className="hint">
        λ y ancho de banda corresponden al centro del recorte. Una diferencia
        visual no demuestra movimiento propio ni variabilidad.
      </p>
    </div>
  );
}
