"""Modelos de entrada de la API, con validación de unidades explícita."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .coordinates import CoordinateError, parse_dec, parse_ra
from .targets import get_preset

__all__ = ["SearchRequest"]


class SearchRequest(BaseModel):
    ra_deg: float | str | None = None
    dec_deg: float | str | None = None
    target_name: str | None = None
    fov_arcmin: float = Field(default=10.0, ge=1.0, le=30.0)
    frames: int = Field(default=12, ge=3, le=16)
    detector: str = Field(default="auto")
    sexagesimal: bool = False

    @model_validator(mode="after")
    def _validate_and_normalize(self) -> SearchRequest:
        has_coordinates = self.ra_deg is not None or self.dec_deg is not None
        if self.target_name and has_coordinates:
            raise ValueError("use target_name o coordenadas explícitas, no ambas entradas")
        if not self.target_name and not has_coordinates:
            raise ValueError("se requiere target_name o el par ra_deg/dec_deg")

        if self.target_name:
            preset = get_preset(self.target_name)
            if preset is None:
                raise ValueError(
                    f"objetivo desconocido: {self.target_name!r}; "
                    "use uno de los cinco presets o coordenadas"
                )
            self.ra_deg = preset.ra_deg
            self.dec_deg = preset.dec_deg
            self.target_name = preset.id

        if self.ra_deg is None or self.dec_deg is None:
            raise ValueError("faltan ra_deg y dec_deg")

        try:
            self.ra_deg = parse_ra(self.ra_deg, sexagesimal=self.sexagesimal)
            self.dec_deg = parse_dec(self.dec_deg, sexagesimal=self.sexagesimal)
        except CoordinateError as exc:
            raise ValueError(str(exc)) from exc

        detector = self.detector.strip().upper()
        if detector != "AUTO" and detector not in {f"D{index}" for index in range(1, 7)}:
            raise ValueError("detector debe ser 'auto' o D1…D6")
        self.detector = detector

        return self

    def normalized(self) -> dict[str, object]:
        """Representación estable usada por la cola y el manifiesto."""

        normalized = {
            "ra_deg": round(float(self.ra_deg), 8),
            "dec_deg": round(float(self.dec_deg), 8),
            "fov_arcmin": float(self.fov_arcmin),
            "frames": int(self.frames),
            "detector": self.detector,
            "target_name": self.target_name,
        }
        if self.target_name:
            preset = get_preset(self.target_name)
            normalized.update(coordinate_epoch_jyear=preset.epoch_jyear,
                              coordinate_reference=preset.reference,
                              coordinate_model=preset.coordinate_model,
                              astrometry_fitted_to_spherex=False)
        return normalized
