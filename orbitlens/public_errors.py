"""Mensajes públicos estables: nunca devolver traceback/rutas internas."""

import httpx

from .downloads import DownloadError
from .execution import DeadlineExceeded
from .storage import StorageError


def public_failure(exc: Exception) -> str:
    if isinstance(exc, DeadlineExceeded):
        return "se agotó el presupuesto temporal; puede volver a intentarlo"
    if isinstance(exc, StorageError):
        return "espacio de almacenamiento insuficiente; contacte con el operador"
    if isinstance(exc, DownloadError):
        cause = exc.__cause__
        if isinstance(cause, httpx.HTTPStatusError):
            return f"el archivo remoto devolvió HTTP {cause.response.status_code}"
        return "no se pudo obtener un FITS remoto válido dentro de los límites"
    message = str(exc)
    # Solo estos diagnósticos son generados por nosotros sin rutas ni URLs.
    if message.startswith(("cobertura válida", "el detector del FITS contradice", "el OBSID del FITS contradice",
                           "MJD-OBS del FITS contradice", "FITS sin detector reconocible",
                           "la coordenada solicitada queda fuera del recorte FITS")):
        return message[:240]
    return "no se pudo procesar el trabajo o recorte; inténtelo de nuevo o contacte con el operador"
