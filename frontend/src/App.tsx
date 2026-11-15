import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchManifest,
  fetchPresets,
  fetchStatus,
  startSearch,
} from "./api";
import SearchForm, { type FormValues } from "./SearchForm";
import StatusPanel from "./StatusPanel";
import Viewer from "./Viewer";
import ResourcesPanel from "./ResourcesPanel";
import type { Job, Manifest, Preset, SearchPayload } from "./types";

const TERMINAL: Job["status"][] = ["ready", "partial", "empty", "error"];

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function readInitialValues(): FormValues {
  const params = new URLSearchParams(window.location.search);
  const fov = Number(params.get("fov") ?? "10");
  const frames = Number(params.get("frames") ?? "12");
  return {
    presetId: params.get("target") ?? "",
    ra: params.get("ra") ?? "",
    dec: params.get("dec") ?? "",
    sexagesimal: params.get("sexagesimal") === "1",
    fovArcmin: Number.isFinite(fov) && fov >= 1 && fov <= 30 ? fov : 10,
    frames:
      Number.isFinite(frames) && frames >= 3 && frames <= 16 ? frames : 12,
    detector: params.get("detector") ?? "auto",
  };
}

export default function App() {
  const [presets, setPresets] = useState<Preset[]>([]);
  const [values, setValues] = useState<FormValues>(readInitialValues);
  const [job, setJob] = useState<Job | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const pollTimer = useRef<number | null>(null);
  const initialResult = useRef<string | null>(
    new URLSearchParams(window.location.search).get("result"),
  );

  useEffect(() => {
    fetchPresets()
      .then(setPresets)
      .catch((reason: unknown) => setError(messageOf(reason)));
  }, []);

  useEffect(() => {
    const resultId = initialResult.current;
    if (!resultId) {
      return;
    }
    initialResult.current = null;
    setBusy(true);
    fetchManifest(resultId)
      .then((loaded) => {
        setManifest(loaded);
        setBusy(false);
      })
      .catch((reason: unknown) => {
        setError(messageOf(reason));
        setBusy(false);
      });
  }, []);

  useEffect(
    () => () => {
      if (pollTimer.current !== null) {
        window.clearTimeout(pollTimer.current);
      }
    },
    [],
  );

  useEffect(() => {
    if (
      !values.presetId ||
      values.ra ||
      values.dec ||
      presets.length === 0
    ) {
      return;
    }
    const preset = presets.find((item) => item.id === values.presetId);
    if (preset) {
      setValues((current) => ({
        ...current,
        ra: preset.ra_deg.toFixed(6),
        dec: preset.dec_deg.toFixed(6),
      }));
    }
  }, [presets, values.presetId, values.ra, values.dec]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (values.presetId) {
      params.set("target", values.presetId);
    }
    if (values.ra) {
      params.set("ra", values.ra);
    }
    if (values.dec) {
      params.set("dec", values.dec);
    }
    if (values.sexagesimal) {
      params.set("sexagesimal", "1");
    }
    params.set("fov", String(values.fovArcmin));
    params.set("frames", String(values.frames));
    if (values.detector !== "auto") {
      params.set("detector", values.detector);
    }
    if (manifest?.result_id) {
      params.set("result", manifest.result_id);
    }
    const query = params.toString();
    window.history.replaceState(
      null,
      "",
      `${window.location.pathname}${query ? `?${query}` : ""}`,
    );
  }, [values, manifest?.result_id]);

  const poll = useCallback((jobId: string) => {
    const tick = async () => {
      try {
        const status = await fetchStatus(jobId);
        setJob(status);
        if (!TERMINAL.includes(status.status)) {
          pollTimer.current = window.setTimeout(tick, 1000);
          return;
        }
        setBusy(false);
        if (status.result_id) {
          try {
            const result = await fetchManifest(status.result_id);
            setManifest(result);
          } catch (reason) {
            setError(messageOf(reason));
          }
        }
      } catch (reason) {
        setError(messageOf(reason));
        setBusy(false);
      }
    };
    void tick();
  }, []);

  const handleSubmit = useCallback(async () => {
    if (pollTimer.current !== null) {
      window.clearTimeout(pollTimer.current);
    }
    setError(null);
    setJob(null);
    setManifest(null);

    if (!values.presetId && (!values.ra.trim() || !values.dec.trim())) {
      setError("Introduce RA y Dec, o elige uno de los cinco objetivos.");
      return;
    }

    const payload: SearchPayload = {
      fov_arcmin: values.fovArcmin,
      frames: values.frames,
      detector: values.detector,
    };
    if (values.presetId) {
      payload.target_name = values.presetId;
    } else {
      payload.ra_deg = values.ra.trim();
      payload.dec_deg = values.dec.trim();
      payload.sexagesimal = values.sexagesimal;
    }

    setBusy(true);
    try {
      const started = await startSearch(payload);
      setJob({
        job_id: started.job_id,
        status: started.status,
        phase: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        result_id: null,
        error: null,
        warnings: [],
        counts: {},
        request: {},
        status_url: started.status_url,
      });
      poll(started.job_id);
    } catch (reason) {
      setError(messageOf(reason));
      setBusy(false);
    }
  }, [poll, values]);

  return (
    <div className="app">
      <a className="skip-link" href="#contenido-principal">
        Saltar al contenido principal
      </a>

      <header className="topbar">
        <a className="brand" href="/" aria-label="OrbitLens, inicio">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" role="presentation" focusable="false">
              <circle cx="16" cy="16" r="5.2" className="mark-core" />
              <ellipse cx="16" cy="16" rx="13.2" ry="6.4" className="mark-orbit" />
              <circle cx="27" cy="12" r="1.9" className="mark-dot" />
            </svg>
          </span>
          <span className="brand-text">
            <strong>OrbitLens</strong>
            <small>SPHEREx temporal explorer</small>
          </span>
        </a>
        <nav className="topnav" aria-label="Secciones de la aplicación">
          <a href="#campo">Campo</a>
          <a href="#estado">Estado</a>
          <a href="#visor">Visor</a>
          <a href="#recursos">Recursos</a>
        </nav>
        <span className="mission-pill">
          <span className="mission-dot" aria-hidden="true" />
          DR1 + QR3
        </span>
      </header>

      <header className="hero">
        <div className="hero-copy">
          <p className="eyebrow">
            NASA Space Apps 2026 · Planet X and SPHEREx
          </p>
          <h1>OrbitLens</h1>
          <p className="lede">
            Secuencias temporales de imágenes infrarrojas de SPHEREx para un
            campo celeste.
          </p>
          <p className="hero-note">
            Datos públicos de IRSA (DR1 + QR3). Una secuencia no implica
            detección ni movimiento confirmado.
          </p>
          <div className="hero-actions">
            <a className="primary link-button" href="#campo">
              Construir una secuencia
            </a>
            <a className="ghost link-button" href="#visor">
              Explorar el visor
            </a>
          </div>
        </div>
        <div className="hero-orbit" aria-hidden="true">
          <svg viewBox="0 0 260 260" role="presentation" focusable="false">
            <defs>
              <linearGradient id="orbitStroke" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#7dd3fc" stopOpacity="0.9" />
                <stop offset="0.55" stopColor="#a78bfa" stopOpacity="0.55" />
                <stop offset="1" stopColor="#ff8a3d" stopOpacity="0.85" />
              </linearGradient>
              <radialGradient id="orbitCore" cx="0.35" cy="0.3" r="0.8">
                <stop offset="0" stopColor="#fff7ed" />
                <stop offset="0.55" stopColor="#ffb37a" />
                <stop offset="1" stopColor="#c2410c" />
              </radialGradient>
            </defs>
            <circle cx="130" cy="130" r="118" className="orbit-halo" />
            <circle
              cx="130"
              cy="130"
              r="92"
              className="orbit-ring"
              stroke="url(#orbitStroke)"
            />
            <ellipse cx="130" cy="130" rx="118" ry="42" className="orbit-path" />
            <ellipse
              cx="130"
              cy="130"
              rx="76"
              ry="118"
              className="orbit-path orbit-path-vertical"
            />
            <circle cx="130" cy="130" r="30" fill="url(#orbitCore)" className="orbit-core" />
            <circle cx="230" cy="150" r="4.5" className="orbit-satellite" />
            <circle cx="54" cy="84" r="2.6" className="orbit-satellite faint" />
          </svg>
          <span className="orbit-caption">SPHEREx · 0.75–5 µm</span>
        </div>
      </header>

      <dl className="mission-stats" aria-label="Ficha de la misión">
        <div>
          <dt>Misión</dt>
          <dd>SPHEREx</dd>
        </div>
        <div>
          <dt>Archivo</dt>
          <dd>IRSA · NASA/IPAC</dd>
        </div>
        <div>
          <dt>Colecciones</dt>
          <dd>DR1 + QR3</dd>
        </div>
        <div>
          <dt>Época de centros</dt>
          <dd>J2026</dd>
        </div>
      </dl>

      <main className="layout" id="contenido-principal" tabIndex={-1}>
        <section className="column" aria-label="Control y estado">
          <SearchForm
            presets={presets}
            values={values}
            busy={busy}
            onChange={setValues}
            onSubmit={handleSubmit}
          />
          <StatusPanel job={job} error={error} busy={busy} />
          <ResourcesPanel
            values={values}
            presets={presets}
            grid={manifest?.grid}
          />
        </section>

        <section className="column viewer-column" id="visor" aria-label="Visor de la secuencia">
          {manifest ? (
            <Viewer manifest={manifest} />
          ) : (
            <div className="panel placeholder">
              <div className="placeholder-orbit" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
              <p className="eyebrow">Visor de secuencias</p>
              <h2>
                {busy ? "Preparando la secuencia…" : "Sin secuencia cargada"}
              </h2>
              <p>
                {busy
                  ? "Consultando IRSA, descargando recortes y alineando las imágenes."
                  : "Elige uno de los cinco campos de prueba o introduce coordenadas para comenzar."}
              </p>
              <p className="placeholder-note">
                Cada resultado incluye PNG, FITS derivados, manifiesto y
                metadatos de cobertura y máscaras.
              </p>
            </div>
          )}
        </section>
      </main>

      <footer className="footer">
        <div className="footer-brand">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" role="presentation" focusable="false">
              <circle cx="16" cy="16" r="5.2" className="mark-core" />
              <ellipse cx="16" cy="16" rx="13.2" ry="6.4" className="mark-orbit" />
              <circle cx="27" cy="12" r="1.9" className="mark-dot" />
            </svg>
          </span>
          <div>
            <strong>OrbitLens</strong>
            <p>Secuencias temporales SPHEREx · NASA Space Apps 2026</p>
          </div>
        </div>
        <div className="footer-meta">
          <p>Datos: NASA/IPAC IRSA · DR1 + QR3 · centros J2026</p>
          <p>
            Los recortes son derivados del proyecto; no sustituyen los FITS
            originales. No se declara detección ni validación científica.
          </p>
        </div>
      </footer>
    </div>
  );
}
