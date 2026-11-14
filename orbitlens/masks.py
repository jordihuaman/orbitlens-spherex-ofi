"""Máscaras de calidad a partir del mapa ``FLAGS`` de SPHEREx.

No se asume una numeración fija de bits: las definiciones ``MSKN*``/``MSKD*``
se leen de la cabecera del propio FITS. Si no existen, solo se descartan valores
no finitos, en lugar de inventar bits.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

__all__ = [
    "DEFAULT_REJECT_NAMES",
    "FlagDefinitions",
    "parse_flag_bits",
    "resolve_flag_bits",
    "compute_valid_mask",
]

# Nombres que el protocolo propone enmascarar para visualización. Solo se
# aplican si la cabecera del FITS define su bit.
DEFAULT_REJECT_NAMES = frozenset(
    {
        "TRANSIENT",
        "OVERFLOW",
        "SUR_ERROR",
        "NONFUNC",
        "DICHROIC",
        "MISSING_DATA",
        "HOT",
        "COLD",
        "PHANMISS",
        "NONLINEAR",
        "PERSIST",
        "OUTLIER",
        "CROSSTALK",
        "GHOST",
        "GHOST_FPA",
        "GHOST_EXT",
        "STREAK",
        "BLOOM",
        "SNOWBALL",
        "HALO",
        "SATELLITE_HALO",
    }
)


@dataclass(frozen=True)
class FlagDefinitions:
    bits: dict[str, int]
    source: str
    warnings: tuple[str, ...] = ()


def _numeric(text: str) -> bool:
    return bool(re.fullmatch(r"[+-]?\d+", text.strip()))


def parse_flag_bits(header) -> dict[str, int]:
    """Extrae ``NOMBRE -> bit`` de las claves ``MSKN#`` y ``MSKD#``.

    El número de bit es el sufijo de la clave. ``MSKN#`` aporta el nombre
    corto; ``MSKD#`` se usa como respaldo descriptivo si falta el nombre.
    """

    bits: dict[str, int] = {}
    covered: set[int] = set()
    for prefix in ("N", "D"):
        for key in header:
            match = re.fullmatch(r"MSK([ND])(\d+)", str(key).strip().upper())
            if not match or match.group(1) != prefix:
                continue
            index = int(match.group(2))
            if index in covered or not (0 <= index < 63):
                continue
            value = str(header[key]).strip()
            if not value or _numeric(value):
                continue
            bits.setdefault(value.upper(), index)
            covered.add(index)
    return bits


def resolve_flag_bits(header) -> FlagDefinitions:
    """Devuelve las definiciones disponibles y advertencias honestas."""

    bits = parse_flag_bits(header)
    if not bits:
        return FlagDefinitions(
            bits={},
            source="none",
            warnings=(
                "FLAGS sin definiciones MSKN/MSKD: solo se descartan valores "
                "no finitos; no se aplica enmascarado por bits",
            ),
        )

    missing = sorted(DEFAULT_REJECT_NAMES - set(bits))
    warnings: tuple[str, ...] = ()
    if missing:
        preview = ", ".join(missing[:6])
        suffix = "…" if len(missing) > 6 else ""
        warnings = (
            f"{len(missing)} bits de rechazo sin definición en la cabecera "
            f"({preview}{suffix}); no se enmascaran",
        )
    return FlagDefinitions(bits=bits, source="header", warnings=warnings)


def compute_valid_mask(
    flags: np.ndarray,
    definitions: FlagDefinitions,
    reject_names: frozenset[str] = DEFAULT_REJECT_NAMES,
) -> np.ndarray:
    """Devuelve ``True`` donde el píxel es utilizable.

    Los valores negativos, NaN e Inf se consideran inválidos. Los bits de
    rechazo solo se aplican si están definidos en la cabecera.
    """

    values = np.asarray(flags, dtype=np.float64)
    valid = np.isfinite(values) & (values >= 0)

    integer_flags = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0).astype(
        np.int64
    )
    for name in reject_names:
        bit = definitions.bits.get(name.upper())
        if bit is None:
            continue
        valid &= (integer_flags & (1 << bit)) == 0
    return valid
