from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class WebOSException(Exception):
    status_code: int = 500
    detail: str = "Internal Server Error"

    def __init__(self, detail: Optional[str] = None):
        if detail:
            self.detail = detail


class EntityNotFound(WebOSException):
    status_code = 404
    detail = "Entity not found"


class PermissionDenied(WebOSException):
    status_code = 403
    detail = "Permission denied"


class ValidationError(WebOSException):
    status_code = 400
    detail = "Validation error"


async def webos_exception_handler(request: Request, exc: WebOSException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": exc.__class__.__name__},
    )


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(WebOSException, webos_exception_handler)
    # Could add more specific handlers here
