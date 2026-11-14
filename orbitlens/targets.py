"""Los cinco campos de prueba exigidos por el reto.

Centros ICRS propagados a J2026 desde un snapshot SIMBAD J2000 con movimiento
propio tangencial. No son un ajuste a píxeles SPHEREx ni confirman detección.
"""

from __future__ import annotations

import unicodedata
from dataclasses import asdict, dataclass

from .astrometry import SNAPSHOT, position_at

_CENTERS = {target: position_at(target, 2026.0) for target in SNAPSHOT["entries"]}

__all__ = ["Preset", "PRESETS", "get_preset", "public_presets"]


@dataclass(frozen=True)
class Preset:
    id: str
    name: str
    ra_deg: float
    dec_deg: float
    reference: str
    note: str
    verified: bool = False
    aliases: tuple[str, ...] = ()
    epoch_jyear: float = 2026.0
    coordinate_model: str = "SIMBAD J2000 + movimiento tangencial a J2026; sin paralaje/RV/órbita"

    def public(self) -> dict[str, object]:
        data = asdict(self)
        data.pop("aliases", None)
        return data


PRESETS: tuple[Preset, ...] = (
    Preset(
        id="barnard",
        name="Estrella de Barnard",
        ra_deg=_CENTERS["barnard"][0],
        dec_deg=_CENTERS["barnard"][1],
        reference="GJ 699, ICRS J2026 aproximado; SIMBAD/2020yCat.1350....0G, PM desde J2000",
        note=(
            "Enana roja de alto movimiento propio. Coordenada de catálogo para "
            "centrar el campo; verificar época y movimiento propio antes de "
            "interpretar desplazamientos."
        ),
        aliases=("barnard", "barnard's star", "estrella de barnard", "gj 699"),
    ),
    Preset(
        id="epsindi_b",
        name="Epsilon Indi B",
        ra_deg=_CENTERS["epsindi_b"][0],
        dec_deg=_CENTERS["epsindi_b"][1],
        reference="Epsilon Indi B, ICRS J2026 aproximado; SIMBAD/2020yCat.1350....0G, PM desde J2000",
        note=(
            "Centro aproximado de la compañera B, a unos 6.7 arcmin de Epsilon "
            "Indi A. Confirmar la separación y la época de la referencia."
        ),
        aliases=("epsindi_b", "epsilon indi b", "eps ind b", "epsindi b"),
    ),
    Preset(
        id="wise0855",
        name="WISE 0855−0714",
        ra_deg=_CENTERS["wise0855"][0],
        dec_deg=_CENTERS["wise0855"][1],
        reference="WISEA J085510.74−071442.5, ICRS J2026 aproximado; SIMBAD/2021ApJS..253....7K, PM desde J2000",
        note=(
            "Enana marrón fría con gran movimiento propio. La cobertura SPHEREx "
            "debe comprobarse por campo; no se asume detección."
        ),
        aliases=("wise0855", "wise 0855", "wise 0855-0714", "wise0855-0714"),
    ),
    Preset(
        id="rw_aur",
        name="RW Aurigae",
        ra_deg=_CENTERS["rw_aur"][0],
        dec_deg=_CENTERS["rw_aur"][1],
        reference="RW Aur, ICRS J2026 aproximado; SIMBAD/2007A&A...474..653V, PM desde J2000",
        note=(
            "Estrella joven con variabilidad y eyecciones. Comparar épocas exige "
            "declarar que la variabilidad intrínseca puede dominar la señal."
        ),
        aliases=("rw_aur", "rw aur", "rw aurigae"),
    ),
    Preset(
        id="r_dra",
        name="R Draconis",
        ra_deg=_CENTERS["r_dra"][0],
        dec_deg=_CENTERS["r_dra"][1],
        reference="R Dra, ICRS J2026 aproximado; SIMBAD/2020yCat.1350....0G, PM desde J2000",
        note=(
            "Gigante variable de largo periodo. Las diferencias entre épocas "
            "pueden reflejar el ciclo estelar, no movimiento propio."
        ),
        aliases=("r_dra", "r dra", "r draconis"),
    ),
)


def _normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.strip().lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def get_preset(name_or_id: str) -> Preset | None:
    """Busca un preset por id, nombre o alias (sin distinguir mayúsculas)."""

    needle = _normalize(name_or_id)
    for preset in PRESETS:
        candidates = (preset.id, preset.name, *preset.aliases)
        if any(_normalize(candidate) == needle for candidate in candidates):
            return preset
    return None


def public_presets() -> list[dict[str, object]]:
    return [preset.public() for preset in PRESETS]
