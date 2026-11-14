import type { Preset } from "./types";

export interface FormValues {
  presetId: string;
  ra: string;
  dec: string;
  sexagesimal: boolean;
  fovArcmin: number;
  frames: number;
  detector: string;
}

interface Props {
  presets: Preset[];
  values: FormValues;
  busy: boolean;
  onChange: (values: FormValues) => void;
  onSubmit: () => void;
}

const FRAME_OPTIONS = Array.from({ length: 14 }, (_, index) => index + 3);
const DETECTORS = ["auto", "D1", "D2", "D3", "D4", "D5", "D6"];

export default function SearchForm({
  presets,
  values,
  busy,
  onChange,
  onSubmit,
}: Props) {
  const preset = presets.find((item) => item.id === values.presetId);
  const update = (patch: Partial<FormValues>) =>
    onChange({ ...values, ...patch });

  const handlePreset = (presetId: string) => {
    if (!presetId) {
      update({ presetId: "" });
      return;
    }
    const preset = presets.find((item) => item.id === presetId);
    if (!preset) {
      return;
    }
    update({
      presetId,
      ra: preset.ra_deg.toFixed(6),
      dec: preset.dec_deg.toFixed(6),
    });
  };

  return (
    <form
      className="panel search-panel"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Campo de observación</p>
          <h2>Buscar secuencia</h2>
        </div>
        <span className="badge">DR1 + QR3</span>
      </div>

      <label className="field">
        <span>Objetivo de prueba</span>
        <select
          value={values.presetId}
          onChange={(event) => handlePreset(event.target.value)}
        >
          <option value="">Coordenadas manuales</option>
          {presets.map((preset) => (
            <option key={preset.id} value={preset.id}>
              {preset.name}
            </option>
          ))}
        </select>
      </label>

      {preset && (
        <p className="hint">
          {preset.reference}. {preset.note}
          {!preset.verified && " Referencia pendiente de verificación astrométrica."}
        </p>
      )}

      <div className="field-row">
        <label className="field">
          <span>RA {values.sexagesimal ? "(horas)" : "(grados)"}</span>
          <input
            type="text"
            inputMode="decimal"
            placeholder={values.sexagesimal ? "17 57 48.5" : "269.45208"}
            value={values.ra}
            onChange={(event) =>
              update({ ra: event.target.value, presetId: "" })
            }
            required={!values.presetId}
          />
        </label>
        <label className="field">
          <span>Dec (grados)</span>
          <input
            type="text"
            inputMode="decimal"
            placeholder={values.sexagesimal ? "+04 41 36" : "4.69339"}
            value={values.dec}
            onChange={(event) =>
              update({ dec: event.target.value, presetId: "" })
            }
            required={!values.presetId}
          />
        </label>
      </div>

      <label className="checkbox">
        <input
          type="checkbox"
          checked={values.sexagesimal}
          onChange={(event) =>
            update({ sexagesimal: event.target.checked })
          }
        />
        <span>Entrada sexagesimal (RA en horas, Dec en grados)</span>
      </label>

      <label className="field">
        <span>
          Campo de visión: <strong>{values.fovArcmin}′</strong> de ancho
        </span>
        <input
          type="range"
          min={1}
          max={30}
          step={1}
          value={values.fovArcmin}
          onChange={(event) =>
            update({ fovArcmin: Number(event.target.value) })
          }
        />
      </label>

      <div className="field-row">
        <label className="field">
          <span>Frames solicitados</span>
          <select
            value={values.frames}
            onChange={(event) =>
              update({ frames: Number(event.target.value) })
            }
          >
            {FRAME_OPTIONS.map((count) => (
              <option key={count} value={count}>
                {count}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Detector</span>
          <select
            value={values.detector}
            onChange={(event) => update({ detector: event.target.value })}
          >
            {DETECTORS.map((detector) => (
              <option key={detector} value={detector}>
                {detector === "auto" ? "Automático" : detector}
              </option>
            ))}
          </select>
        </label>
      </div>

      <p className="hint">
        El FOV es el ancho completo de la imagen de salida. El centro permanece
        fijo entre épocas; no se recentra sobre el objeto.
      </p>

      <button className="primary" type="submit" disabled={busy}>
        {busy ? "Procesando…" : "Buscar secuencia"}
      </button>
    </form>
  );
}
