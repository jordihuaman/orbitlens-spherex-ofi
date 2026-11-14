"""Interpretación y validación de coordenadas celestes.

Reglas del proyecto:
- Decimal: RA en grados ``[0, 360)`` y Dec en grados ``[-90, 90]``.
- Sexagesimal: RA en horas y Dec en grados. El modo debe ser explícito.
"""

from __future__ import annotations

import math
import re

__all__ = [
    "CoordinateError",
    "parse_ra",
    "parse_dec",
    "parse_pair",
    "validate_ra",
    "validate_dec",
    "format_sexagesimal",
]


class CoordinateError(ValueError):
    """Entrada de coordenadas inválida o ambigua."""


def _finite(value: object, field: str) -> float:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise CoordinateError(f"{field} no es un número válido: {value!r}") from exc
    if not math.isfinite(number):
        raise CoordinateError(f"{field} debe ser finito, se recibió {value!r}")
    return number


def validate_ra(ra_deg: float) -> float:
    """Valida una ascensión recta decimal en grados."""

    if not math.isfinite(ra_deg):
        raise CoordinateError("RA debe ser finita")
    if not (0.0 <= ra_deg < 360.0):
        raise CoordinateError(
            f"RA fuera de rango: {ra_deg}. Use grados en [0, 360); 360 equivale a 0."
        )
    return ra_deg


def validate_dec(dec_deg: float) -> float:
    """Valida una declinación decimal en grados."""

    if not math.isfinite(dec_deg):
        raise CoordinateError("Dec debe ser finita")
    if not (-90.0 <= dec_deg <= 90.0):
        raise CoordinateError(f"Dec fuera de rango: {dec_deg}. Use grados en [-90, 90].")
    return dec_deg


def _sexagesimal_parts(value: object, field: str) -> tuple[int, float, float, float]:
    raw = str(value).strip().replace("\u2212", "-")
    if not raw:
        raise CoordinateError(f"{field} está vacío")

    sign = 1
    if raw[0] in "+-":
        sign = -1 if raw[0] == "-" else 1
        raw = raw[1:]

    parts = re.findall(r"\d+(?:\.\d+)?", raw)
    if len(parts) != 3:
        raise CoordinateError(
            f"{field} sexagesimal debe tener tres componentes (g/h, m, s): {value!r}"
        )

    first, minutes, seconds = (float(part) for part in parts)
    if not all(math.isfinite(number) for number in (first, minutes, seconds)):
        raise CoordinateError(f"{field} contiene componentes no finitos")
    if not (0.0 <= minutes < 60.0):
        raise CoordinateError(f"{field}: los minutos deben estar en [0, 60)")
    if not (0.0 <= seconds < 60.0):
        raise CoordinateError(f"{field}: los segundos deben estar en [0, 60)")
    return sign, first, minutes, seconds


def parse_ra(value: object, *, sexagesimal: bool = False) -> float:
    """Devuelve RA en grados. En modo sexagesimal la entrada son horas."""

    if not sexagesimal:
        return validate_ra(_finite(value, "RA"))

    sign, hours, minutes, seconds = _sexagesimal_parts(value, "RA")
    if sign < 0:
        raise CoordinateError("RA no puede ser negativa")
    if hours >= 24.0:
        raise CoordinateError(f"RA en horas debe estar en [0, 24): {value!r}")
    return validate_ra((hours + minutes / 60.0 + seconds / 3600.0) * 15.0)


def parse_dec(value: object, *, sexagesimal: bool = False) -> float:
    """Devuelve Dec en grados. En modo sexagesimal la entrada son grados."""

    if not sexagesimal:
        return validate_dec(_finite(value, "Dec"))

    sign, degrees, minutes, seconds = _sexagesimal_parts(value, "Dec")
    if degrees > 90.0:
        raise CoordinateError(f"Dec en grados debe estar en [-90, 90]: {value!r}")
    if degrees == 90.0 and (minutes or seconds):
        raise CoordinateError("Dec = 90° solo admite 0 minutos y 0 segundos")
    magnitude = degrees + minutes / 60.0 + seconds / 3600.0
    return validate_dec(sign * magnitude)


def parse_pair(
    ra: object, dec: object, *, sexagesimal: bool = False
) -> tuple[float, float]:
    """Normaliza un par RA/Dec y devuelve ``(ra_deg, dec_deg)``."""

    return parse_ra(ra, sexagesimal=sexagesimal), parse_dec(dec, sexagesimal=sexagesimal)


def format_sexagesimal(ra_deg: float, dec_deg: float) -> tuple[str, str]:
    """Formatea coordenadas decimales como texto sexagesimal legible."""

    ra_deg = validate_ra(ra_deg)
    dec_deg = validate_dec(dec_deg)

    total_hours = ra_deg / 15.0
    hours = int(total_hours)
    minutes_float = (total_hours - hours) * 60.0
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60.0
    ra_text = f"{hours:02d}h{minutes:02d}m{seconds:04.1f}s"

    sign = "-" if dec_deg < 0 else "+"
    magnitude = abs(dec_deg)
    degrees = int(magnitude)
    minutes_float = (magnitude - degrees) * 60.0
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60.0
    dec_text = f"{sign}{degrees:02d}°{minutes:02d}′{seconds:04.1f}″"
    return ra_text, dec_text
