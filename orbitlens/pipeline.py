"""Lectura FITS, máscaras, reproyección y render de imágenes SPHEREx.

El módulo separa funciones puras (fáciles de probar con datos sintéticos) de la
orquestación de red, que vive en ``service.py``.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from reproject import reproject_interp

from .masks import FlagDefinitions, compute_valid_mask, resolve_flag_bits

__all__ = [
    "PipelineError",
    "SpherexImage",
    "ProcessedFrame",
    "build_target_wcs",
    "read_spherex_image",
    "reproject_frame",
    "compute_stretch_limits",
    "asinh_stretch",
    "apply_colormap",
    "render_rgba",
    "write_png",
    "write_derived_fits",
]


class PipelineError(RuntimeError):
    """FITS ausente, corrupto o incompatible con el recorrido temporal."""


@dataclass
class SpherexImage:
    path: Path
    data: np.ndarray
    flags: np.ndarray | None
    header: fits.Header
    wcs: WCS
    flag_definitions: FlagDefinitions
    valid: np.ndarray
    valid_fraction: float
    center_valid: bool
    lambda_um: float | None
    bandwidth_um: float | None
    detector: str | None
    version: str | None
    bunit: str | None
    warnings: tuple[str, ...] = ()


@dataclass
class ProcessedFrame:
    source: SpherexImage
    data: np.ndarray
    valid: np.ndarray

    @property
    def valid_fraction(self) -> float:
        return float(self.valid.mean()) if self.valid.size else 0.0

    @property
    def center_valid(self) -> bool:
        if not self.valid.size:
            return False
        height, width = self.valid.shape
        return bool(self.valid[height // 2, width // 2])


def build_target_wcs(
    ra_deg: float,
    dec_deg: float,
    fov_arcmin: float,
    *,
    pixel_scale_arcsec: float = 6.15,
) -> tuple[WCS, int, int]:
    """Rejilla norte-arriba/este-izquierda, centrada y de tamaño fijo."""

    if not (0 < fov_arcmin <= 60):
        raise PipelineError(f"FOV fuera de rango: {fov_arcmin}")
    if pixel_scale_arcsec <= 0:
        raise PipelineError("pixel_scale_arcsec debe ser positivo")

    size = max(8, int(round(fov_arcmin * 60.0 / pixel_scale_arcsec)))
    scale_deg = pixel_scale_arcsec / 3600.0

    wcs = WCS(naxis=2)
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    wcs.wcs.cunit = ["deg", "deg"]
    wcs.wcs.crval = [float(ra_deg), float(dec_deg)]
    wcs.wcs.crpix = [(size + 1.0) / 2.0, (size + 1.0) / 2.0]
    wcs.wcs.cdelt = [-scale_deg, scale_deg]
    wcs.wcs.set()
    return wcs, size, size


def _normalize_microns(value: float | None) -> float | None:
    """Normaliza longitudes de onda cuando la unidad no es explícita.

    Solo acepta magnitudes plausibles para SPHEREx (0.75–5 µm). Si el valor no
    encaja, devuelve ``None`` en lugar de adivinar.
    """

    if value is None or not math.isfinite(value) or value <= 0:
        return None
    if value < 1e-3:  # metros
        return value * 1e6
    if 0.1 <= value <= 10:  # micrómetros
        return value
    if 100 <= value <= 10_000:  # nanómetros
        return value / 1000.0
    return None


def _spectral_info(
    hdul: fits.HDUList, header: fits.Header, shape: tuple[int, int],
    pixel: tuple[float, float] | None = None,
) -> tuple[float | None, float | None, tuple[str, ...]]:
    warnings: list[str] = []
    y, x = shape[0] // 2, shape[1] // 2
    if pixel is not None:
        x, y = pixel

    lambda_um: float | None = None
    bandwidth_um: float | None = None
    wave_wcs: WCS | None = None
    try:
        # IRSA Data Overview §8b: SIP solo corresponde al WCS celestial.
        # Construir W desde una copia para conservar el WCS espacial intacto.
        spectral_header = header.copy()
        for key in list(spectral_header):
            if re.fullmatch(r"(?:A|B|AP|BP)_(?:ORDER|DMAX|\d+_\d+)", key):
                del spectral_header[key]
        candidate = WCS(spectral_header, fobj=hdul, key="W")
        candidate.sip = None
        if any(
            str(ctype).upper().startswith("WAVE") for ctype in candidate.wcs.ctype
        ):
            wave_wcs = candidate
    except Exception:
        wave_wcs = None

    if wave_wcs is not None:
        axis = next(
            index
            for index, ctype in enumerate(wave_wcs.wcs.ctype)
            if str(ctype).upper().startswith("WAVE")
        )
        try:
            world = wave_wcs.all_pix2world([[x, y]], 0)[0]
            raw = float(world[axis])
            unit = str(wave_wcs.wcs.cunit[axis]).strip().lower()
            if unit in {"m", "meter", "metre"}:
                lambda_um = raw * 1e6
            elif unit in {"um", "micron", "microns", "micrometre", "micrometer"}:
                lambda_um = raw
            elif unit in {"nm", "nanometer", "nanometre"}:
                lambda_um = raw / 1000.0
            elif unit in {"a", "angstrom", "angstroms"}:
                lambda_um = raw / 10_000.0
            else:
                lambda_um = _normalize_microns(raw)
                if lambda_um is not None and unit:
                    warnings.append(f"unidad espectral no reconocida: {unit!r}")
            # DR1: dos ejes WAVE-TAB, el segundo es el ancho de banda.
            if len(world) == 2 and "bandwidth" in str(header.get("WCSNAMEW", "")).lower():
                bandwidth_um = float((float(world[1]) * u.Unit(wave_wcs.wcs.cunit[1])).to_value(u.um))
                if not math.isfinite(bandwidth_um) or bandwidth_um <= 0:
                    bandwidth_um = None
        except Exception as exc:
            warnings.append(f"no se pudo evaluar WCS-WAVE: {exc}")
    else:
        for key in ("CWAVE", "WAVELEN", "WAVE"):
            if key in header:
                lambda_um = _normalize_microns(float(header[key]))
                if lambda_um is not None:
                    warnings.append(f"λ tomada de la clave {key}; no de WCS-WAVE")
                    break

    for key in ("CBAND", "BANDWID", "BWIDTH"):
        if bandwidth_um is None and key in header:
            bandwidth_um = _normalize_microns(float(header[key]))
            if bandwidth_um is not None:
                break

    if lambda_um is None:
        warnings.append("longitud de onda central no disponible en el FITS")
    if bandwidth_um is None:
        warnings.append("ancho de banda no disponible en el FITS")
    return lambda_um, bandwidth_um, tuple(warnings)


def read_spherex_image(path: Path, *, target: tuple[float, float] | None = None,
                       max_pixels: int = 4_194_304) -> SpherexImage:
    """Abre un MEF Level 2 por nombre de HDU y valida el producto temporal."""

    path = Path(path)
    try:
        with path.open("rb") as handle:
            if handle.read(2) == b"\x1f\x8b":
                raise PipelineError("se requiere MEF sin gzip de archivo; se admite compresión FITS por teselas")
        hdul = fits.open(path, memmap=False)
    except (OSError, ValueError) as exc:
        raise PipelineError(f"no se pudo abrir el FITS {path.name}: {exc}") from exc

    with hdul:
        # Comprobar dimensiones antes de materializar arrays/descomprimir teselas.
        for index, hdu in enumerate(hdul):
            if index >= 32:
                raise PipelineError("FITS excede el límite de 32 HDU")
            header = hdu.header
            try:
                def declared_elements(prefix: str, current=header) -> int:
                    axes = int(current.get(prefix, 0))
                    if not 0 <= axes <= 3:
                        raise ValueError("axes")
                    lengths = [int(current.get(f"{prefix}{axis}", 0)) for axis in range(1, axes + 1)]
                    if any(value < 0 for value in lengths):
                        raise ValueError("length")
                    return math.prod(lengths) if lengths else 0

                elements = max(declared_elements("NAXIS"), declared_elements("ZNAXIS"))
                compressed = int(header.get("ZNAXIS", 0)) > 0 or bool(header.get("ZIMAGE", False))
                if (hdu.name in {"IMAGE", "FLAGS"} or compressed) and elements > max_pixels:
                    raise PipelineError("IMAGE/FLAGS excede el límite de píxeles antes de cargar datos")
                bitpix = max(abs(int(header.get("BITPIX", 8))), abs(int(header.get("ZBITPIX", 8))))
                if bitpix * elements // 8 > 64 * 1024 * 1024:
                    raise PipelineError("HDU excede el presupuesto de memoria declarado")
                heap = max(int(header.get("PCOUNT", 0)), int(header.get("ZPCOUNT", 0)))
                if heap > 64 * 1024 * 1024:
                    raise PipelineError("heap FITS excede el presupuesto de memoria declarado")
            except (ValueError, TypeError, OverflowError) as exc:
                raise PipelineError("dimensiones FITS inválidas") from exc
        if "IMAGE" not in hdul:
            raise PipelineError(f"{path.name}: falta la extensión IMAGE")
        image_hdu = hdul["IMAGE"]
        data = np.asarray(image_hdu.data, dtype=np.float64)
        if data.ndim != 2:
            raise PipelineError(
                f"{path.name}: IMAGE debe ser 2D; se recibió forma {data.shape}"
            )
        if data.size == 0:
            raise PipelineError(f"{path.name}: IMAGE está vacío")
        if data.size > max_pixels:
            raise PipelineError("IMAGE excede el límite de píxeles tras descomprimir")

        header = image_hdu.header.copy()
        warnings: list[str] = []

        if "FLAGS" in hdul:
            flags = np.asarray(hdul["FLAGS"].data)
            if flags.size > max_pixels:
                raise PipelineError("FLAGS excede el límite de píxeles tras descomprimir")
            if flags.shape != data.shape:
                warnings.append(
                    f"FLAGS {flags.shape} no coincide con IMAGE {data.shape}; "
                    "se ignoran los bits"
                )
                flags = None
            flag_definitions = resolve_flag_bits(hdul["FLAGS"].header)
        else:
            flags = None
            flag_definitions = resolve_flag_bits(header)
            warnings.append("FITS sin extensión FLAGS; no se aplica máscara por bits")

        warnings.extend(flag_definitions.warnings)

        valid = np.isfinite(data)
        if flags is not None:
            valid &= compute_valid_mask(flags, flag_definitions)
        if not valid.any():
            raise PipelineError(f"{path.name}: ningún píxel válido tras aplicar máscaras")

        try:
            celestial = WCS(header, naxis=2).celestial
        except Exception as exc:
            raise PipelineError(f"{path.name}: WCS celestial inválido: {exc}") from exc
        if not celestial.has_celestial:
            raise PipelineError(f"{path.name}: el WCS no contiene ejes celestiales")

        pixel = None
        if target is not None:
            px, py = celestial.world_to_pixel_values(*target)
            if not (math.isfinite(px) and math.isfinite(py)
                    and -0.5 <= px < data.shape[1] - 0.5
                    and -0.5 <= py < data.shape[0] - 0.5):
                raise PipelineError("la coordenada solicitada queda fuera del recorte FITS")
            pixel = (float(px), float(py))
        lambda_um, bandwidth_um, spectral_warnings = _spectral_info(
            hdul, header, data.shape, pixel
        )
        warnings.extend(spectral_warnings)

        height, width = data.shape
        center_valid = bool(valid[height // 2, width // 2])

        return SpherexImage(
            path=path,
            data=data,
            flags=flags,
            header=header,
            wcs=celestial,
            flag_definitions=flag_definitions,
            valid=valid,
            valid_fraction=float(valid.mean()),
            center_valid=center_valid,
            lambda_um=lambda_um,
            bandwidth_um=bandwidth_um,
            detector=str(header.get("DETECTOR", "")).strip() or None,
            version=str(hdul[0].header.get("VERSION", header.get("VERSION", ""))).strip() or None,
            bunit=str(header.get("BUNIT", "")).strip() or None,
            warnings=tuple(dict.fromkeys(warnings)),
        )


def reproject_frame(
    image: SpherexImage,
    target_wcs: WCS,
    shape: tuple[int, int],
) -> ProcessedFrame:
    """Reproyecta brillo superficial y propaga la validez de forma conservadora."""

    try:
        data_out, footprint = reproject_interp(
            (image.data, image.wcs),
            target_wcs,
            shape_out=shape,
            return_footprint=True,
        )
        valid_out, _ = reproject_interp(
            (image.valid.astype(np.float32), image.wcs),
            target_wcs,
            shape_out=shape,
            return_footprint=True,
        )
    except Exception as exc:
        raise PipelineError(f"fallo al reproyectar {image.path.name}: {exc}") from exc

    valid = (
        np.asarray(footprint, dtype=bool)
        & np.isfinite(data_out)
        & (np.asarray(valid_out, dtype=np.float64) >= 0.999)
    )
    data_out = np.where(valid, data_out, np.nan)
    return ProcessedFrame(source=image, data=data_out, valid=valid)


def compute_stretch_limits(
    frames: list[ProcessedFrame],
    *,
    low_percentile: float = 1.0,
    high_percentile: float = 99.5,
) -> tuple[float, float]:
    """Percentiles globales sobre píxeles válidos de toda la secuencia."""

    samples = [frame.data[frame.valid] for frame in frames if frame.valid.any()]
    if not samples:
        raise PipelineError("no hay píxeles válidos para calcular la escala")
    values = np.concatenate(samples)
    vmin, vmax = np.percentile(values, [low_percentile, high_percentile])
    if not (math.isfinite(vmin) and math.isfinite(vmax)) or vmax <= vmin:
        vmin = float(np.min(values))
        vmax = float(np.max(values))
    if vmax <= vmin:
        vmax = vmin + 1.0
    return float(vmin), float(vmax)


def asinh_stretch(
    data: np.ndarray,
    valid: np.ndarray,
    vmin: float,
    vmax: float,
    *,
    softening: float = 0.05,
) -> np.ndarray:
    """Estiramiento asinh normalizado a ``[0, 1]`` (0 en píxeles inválidos)."""

    if vmax <= vmin:
        raise ValueError("vmax debe ser mayor que vmin")
    if not (0 < softening < 1):
        raise ValueError("softening debe estar en (0, 1)")

    scale = (vmax - vmin) * softening
    stretched = np.arcsinh(np.clip((data - vmin) / scale, 0.0, None))
    stretched /= np.arcsinh(1.0 / softening)
    result = np.clip(stretched, 0.0, 1.0)
    return np.where(valid, result, 0.0)


_COLOR_STOPS: tuple[tuple[float, tuple[int, int, int]], ...] = (
    (0.00, (6, 6, 20)),
    (0.22, (35, 16, 72)),
    (0.45, (120, 30, 95)),
    (0.68, (215, 85, 45)),
    (0.86, (250, 180, 80)),
    (1.00, (255, 250, 225)),
)


def apply_colormap(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Convierte valores ``[0, 1]`` en RGBA uint8 con alfa transparente."""

    values = np.clip(np.asarray(values, dtype=np.float64), 0.0, 1.0)
    positions = np.array([stop[0] for stop in _COLOR_STOPS])
    rgba = np.zeros(values.shape + (4,), dtype=np.uint8)
    for channel in range(3):
        colors = np.array([stop[1][channel] for stop in _COLOR_STOPS], dtype=np.float64)
        rgba[..., channel] = np.interp(values, positions, colors).astype(np.uint8)
    rgba[..., 3] = np.where(valid, 255, 0).astype(np.uint8)
    return rgba


def render_rgba(
    frame: ProcessedFrame,
    vmin: float,
    vmax: float,
    *,
    softening: float = 0.05,
) -> np.ndarray:
    stretched = asinh_stretch(
        frame.data, frame.valid, vmin, vmax, softening=softening
    )
    return apply_colormap(stretched, frame.valid)


def write_png(rgba: np.ndarray, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(path, format="PNG", optimize=True)


def write_derived_fits(
    data: np.ndarray,
    wcs: WCS,
    path: Path,
    *,
    metadata: dict[str, object] | None = None,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = wcs.to_header()
    for key, value in (metadata or {}).items():
        if value is None:
            continue
        key = str(key)[:8].upper()
        try:
            header[key] = value
        except (ValueError, TypeError):
            continue
    fits.PrimaryHDU(data=np.asarray(data, dtype=np.float32), header=header).writeto(
        path, overwrite=True, checksum=True
    )
