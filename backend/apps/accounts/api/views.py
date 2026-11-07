"""API views for the accounts app."""

from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .. import selectors, services
from .serializers import GoogleLoginInputSerializer, SessionStateSerializer


@extend_schema(responses=SessionStateSerializer)
@ensure_csrf_cookie
@api_view(["GET"])
def me(request: Request) -> Response:
    """Return the visitor's session state (guest id and signed-in user, if any)."""
    state = selectors.get_session_state(request._request)
    return Response(SessionStateSerializer(state).data)


@extend_schema(request=GoogleLoginInputSerializer, responses=SessionStateSerializer)
@api_view(["POST"])
def google_login(request: Request) -> Response:
    """Verify a Google ID token, sign the user into the session, and claim guest results."""
    data = GoogleLoginInputSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    state = services.sign_in_with_google(request._request, data.validated_data["credential"])
    return Response(SessionStateSerializer(state).data)


@extend_schema(request=None, responses=SessionStateSerializer)
@api_view(["POST"])
def logout(request: Request) -> Response:
    """Sign out of the current session and return the new guest session state."""
    state = services.sign_out(request._request)
    return Response(SessionStateSerializer(state).data)
