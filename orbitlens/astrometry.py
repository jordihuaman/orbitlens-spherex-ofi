"""Predicción tangencial de posición; no ajusta astrometría a los píxeles SPHEREx.

El modelo lineal 3D omite paralaje anual, velocidad radial, aceleraciones y
órbitas de binarias. Adecuado para centrar un campo, no para medir movimientos.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

SNAPSHOT = json.loads(Path(__file__).with_name("catalog_snapshot.json").read_text(encoding="utf-8"))


def position_at(target: str, epoch_jyear: float) -> tuple[float, float]:
    if not math.isfinite(epoch_jyear) or not 1900 <= epoch_jyear <= 2100:
        raise ValueError("época de centrado debe estar entre 1900 y 2100")
    entry = SNAPSHOT["entries"][target]
    ra, dec = np.deg2rad([entry["ra_deg"], entry["dec_deg"]])
    radial = np.array([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])
    east = np.array([-np.sin(ra), np.cos(ra), 0])
    north = np.array([-np.sin(dec) * np.cos(ra), -np.sin(dec) * np.sin(ra), np.cos(dec)])
    velocity = (entry["pmra"] * east + entry["pmdec"] * north) * np.deg2rad(1 / 3600000)
    predicted = radial + (epoch_jyear - SNAPSHOT["epoch_jyear"]) * velocity
    predicted /= np.linalg.norm(predicted)
    return float(np.rad2deg(np.arctan2(predicted[1], predicted[0])) % 360), float(np.rad2deg(np.arcsin(predicted[2])))
