"""Domain exceptions for the accounts app."""

from apps.common.exceptions import DomainError


class InvalidGoogleTokenError(DomainError):
    status_code = 401
    code = "invalid_google_token"
    default_message = "The Google sign-in token is invalid or has expired."


class GoogleAuthNotConfiguredError(DomainError):
    status_code = 503
    code = "google_auth_not_configured"
    default_message = "Google sign-in is not configured on this server."
