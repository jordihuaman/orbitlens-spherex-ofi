export interface Preset {
  id: string;
  name: string;
  ra_deg: number;
  dec_deg: number;
  reference: string;
  note: string;
  verified: boolean;
}

export type JobState =
  | "queued"
  | "running"
  | "ready"
  | "partial"
  | "empty"
  | "error";

export interface Job {
  job_id: string;
  status: JobState;
  phase: string | null;
  created_at: string;
  updated_at: string;
  result_id: string | null;
  error: string | null;
  warnings: string[];
  counts: Record<string, number>;
  request: Record<string, unknown>;
  status_url: string;
}

export interface FrameTime {
  t_min_mjd: number | null;
  t_max_mjd: number | null;
  label: string | null;
}

export interface Frame {
  frame_id: string;
  png: string;
  fits: string;
  obs_id: string;
  collection: string;
  detector: string | null;
  version: string | null;
  time: FrameTime;
  lambda_um: number | null;
  bandwidth_um: number | null;
  valid_fraction: number;
  center_valid: boolean;
  warnings: string[];
}

export interface ManifestFile {
  id: string;
  kind: "png" | "fits";
  path: string;
  sha256: string;
  bytes: number;
}

export interface Grid {
  ra_deg: number;
  dec_deg: number;
  fov_arcmin: number;
  width: number;
  height: number;
  pixel_scale_arcsec: number;
  projection: string;
}

export interface Manifest {
  schema_version: number;
  pipeline_version: string;
  code_commit: string;
  result_id: string;
  created_at: string;
  request: Record<string, unknown>;
  search: Record<string, unknown>;
  grid: Grid;
  processing: Record<string, unknown>;
  frames: Frame[];
  files: ManifestFile[];
  warnings: string[];
}

export interface SearchPayload {
  target_name?: string;
  ra_deg?: string;
  dec_deg?: string;
  sexagesimal?: boolean;
  fov_arcmin: number;
  frames: number;
  detector: string;
}

export interface SearchStart {
  job_id: string;
  status: JobState;
  status_url: string;
  deduplicated: boolean;
}
