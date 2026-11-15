import type { Job } from "./types";

interface Props {
  job: Job | null;
  error: string | null;
  busy: boolean;
}

const STATUS_LABELS: Record<Job["status"], string> = {
  queued: "En cola",
  running: "Procesando",
  ready: "Secuencia lista",
  partial: "Secuencia parcial",
  empty: "Sin datos utilizables",
  error: "Error",
};

const PHASE_LABELS: Record<string, string> = {
  starting: "Iniciando",
  resolving: "Resolviendo coordenadas",
  searching: "Consultando IRSA",
  downloading: "Descargando recortes",
  processing: "Procesando FITS",
  writing: "Escribiendo manifiesto",
};

const COUNT_LABELS: Record<string, string> = {
  collections_queried: "colecciones",
  records_found: "registros",
  candidates: "candidatos",
  selected: "seleccionados",
  downloaded: "descargados",
  attempted: "intentados",
  processed: "procesados",
  failed: "fallidos",
};

const STEPS = ["Cola", "Consulta", "Descarga", "Alineado", "Publicado"];

const PHASE_STEP: Record<string, number> = {
  starting: 0,
  resolving: 0,
  searching: 1,
  downloading: 2,
  processing: 3,
  writing: 4,
};

export default function StatusPanel({ job, error, busy }: Props) {
  if (error) {
    return (
      <div className="panel notice error" role="alert">
        <p className="eyebrow">02 · Estado del trabajo</p>
        <h2>No se pudo completar la búsqueda</h2>
        <p>{error}</p>
        <p className="notice-hint">
          Revisa las coordenadas o inténtalo de nuevo. Los fallos de IRSA no
          implican ausencia de cobertura.
        </p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="panel notice idle" id="estado">
        <p className="eyebrow">02 · Estado del trabajo</p>
        <h2>{busy ? "Conectando con el servicio…" : "Listo para buscar"}</h2>
        <p>
          {busy
            ? "La petición se está registrando en la cola de trabajos."
            : "Los resultados se construyen a partir de imágenes individuales DR1 y QR3 de IRSA."}
        </p>
        <p className="notice-hint">
          La cola se procesa en este servidor; el visor se actualiza
          automáticamente cuando el resultado está publicado.
        </p>
      </div>
    );
  }

  const counts = Object.entries(job.counts).filter(
    ([key]) => COUNT_LABELS[key],
  );
  const activeStep = job.status === "queued" ? 0 : PHASE_STEP[job.phase ?? ""] ?? 0;
  const finished = ["ready", "partial", "empty"].includes(job.status);

  return (
    <div className={`panel status status-${job.status}`} id="estado">
      <div className="status-heading" role="status" aria-live="polite" aria-atomic="true">
        <div>
          <p className="eyebrow">02 · Estado del trabajo</p>
          <h2>{STATUS_LABELS[job.status]}</h2>
        </div>
        <span className={`chip chip-${job.status}`}>{job.status}</span>
      </div>

      {job.phase && (
        <p className="phase">
          {PHASE_LABELS[job.phase] ?? job.phase}
          {job.status === "running" && <span className="pulse" aria-hidden />}
        </p>
      )}
      {job.status === "queued" && job.queue_position != null && (
        <p className="queue-note">Posición en cola: {job.queue_position}</p>
      )}

      <ol className="phase-track" aria-label="Progreso del trabajo">
        {STEPS.map((step, index) => (
          <li
            key={step}
            className={
              finished
                ? "phase-step done"
                : index < activeStep
                  ? "phase-step done"
                  : index === activeStep
                    ? "phase-step current"
                    : "phase-step"
            }
            aria-current={!finished && index === activeStep ? "step" : undefined}
          >
            <span className="phase-dot" aria-hidden="true" />
            <span>{step}</span>
          </li>
        ))}
      </ol>

      {job.status === "empty" && (
        <p>
          La consulta terminó sin frames utilizables. Puede ser falta de
          cobertura, una selección espectral restrictiva o calidad insuficiente;
          no implica que el objeto no exista.
        </p>
      )}

      {job.status === "error" && (
        <p>
          {job.error ??
            "El trabajo falló antes de producir un resultado utilizable."}
        </p>
      )}

      {job.status === "partial" && (
        <p>
          Hay menos frames de los solicitados o algún fallo parcial. La
          secuencia no es exhaustiva. La reproducción requiere al menos tres
          frames.
        </p>
      )}

      {counts.length > 0 && (
        <dl className="counts">
          {counts.map(([key, value]) => (
            <div key={key}>
              <dt>{COUNT_LABELS[key]}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}

      {job.warnings.length > 0 && (
        <details className="warnings">
          <summary>Avisos ({job.warnings.length})</summary>
          <ul>
            {job.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
