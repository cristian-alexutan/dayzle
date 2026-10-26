"""Domain errors and the API exception handler that gives every error the same JSON shape."""

from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class DomainError(Exception):
    """Base class for errors raised by services and selectors.

    Subclasses set ``status_code``, ``code`` and ``default_message``.
    """

    status_code = 400
    code = "domain_error"
    default_message = "The request could not be completed."

    def __init__(self, message: str | None = None, details: Any = None) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


def _error_body(code: str, message: str, details: Any = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def exception_handler(exc: Exception, context: dict) -> Response | None:
    """Format domain and DRF errors as ``{"error": {"code", "message", "details"}}``."""
    if isinstance(exc, DomainError):
        return Response(_error_body(exc.code, exc.message, exc.details), status=exc.status_code)

    if isinstance(exc, Http404):
        exc = drf_exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = drf_exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)
    if response is None or not isinstance(exc, drf_exceptions.APIException):
        return response

    if isinstance(exc, drf_exceptions.ValidationError):
        response.data = _error_body("invalid", "Invalid input.", response.data)
    else:
        response.data = _error_body(exc.default_code, str(exc.detail))
    return response
