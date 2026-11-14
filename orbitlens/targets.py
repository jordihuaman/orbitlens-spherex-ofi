"""Los cinco campos de prueba exigidos por el reto.

Las coordenadas son referencias J2000 aproximadas para *localizar* el campo.
No son una resolución astrométrica nueva ni sustituyen la verificación de Jordi
en SIMBAD/Gaia. La aplicación debe mostrar siempre la procedencia.
"""

from __future__ import annotations

import unicodedata
from dataclasses import asdict, dataclass

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

    def public(self) -> dict[str, object]:
        data = asdict(self)
        data.pop("aliases", None)
        return data


PRESETS: tuple[Preset, ...] = (
    Preset(
        id="barnard",
        name="Estrella de Barnard",
        ra_deg=269.45208,
        dec_deg=4.69339,
        reference="GJ 699 / V* V2500 Oph, J2000 aproximado",
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
        ra_deg=331.04375,
        dec_deg=-56.78264,
        reference="Epsilon Indi B (Ba/Bb), referencia aproximada 22h04m10.5s −56d46m57.5s, J2000",
        note=(
            "Centro aproximado de la compañera B, a unos 6.7 arcmin de Epsilon "
            "Indi A. Confirmar la separación y la época de la referencia."
        ),
        aliases=("epsindi_b", "epsilon indi b", "eps ind b", "epsindi b"),
    ),
    Preset(
        id="wise0855",
        name="WISE 0855−0714",
        ra_deg=133.79512,
        dec_deg=-7.24514,
        reference="WISE J085510.83−071442.5, J2000 aproximado",
        note=(
            "Enana marrón fría con gran movimiento propio. La cobertura SPHEREx "
            "debe comprobarse por campo; no se asume detección."
        ),
        aliases=("wise0855", "wise 0855", "wise 0855-0714", "wise0855-0714"),
    ),
    Preset(
        id="rw_aur",
        name="RW Aurigae",
        ra_deg=76.95633,
        dec_deg=30.40139,
        reference="RW Aur, J2000 aproximado",
        note=(
            "Estrella joven con variabilidad y eyecciones. Comparar épocas exige "
            "declarar que la variabilidad intrínseca puede dominar la señal."
        ),
        aliases=("rw_aur", "rw aur", "rw aurigae"),
    ),
    Preset(
        id="r_dra",
        name="R Draconis",
        ra_deg=248.16750,
        dec_deg=66.75494,
        reference="R Dra, J2000 aproximado",
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
