import uuid
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from apps.common.players import GUEST_ID_SESSION_KEY, get_guest_id


def make_request():
    request = RequestFactory().get("/")
    SessionMiddleware(lambda r: None).process_request(request)
    return request


def test_guest_id_is_created_once_and_stored_in_the_session():
    request = make_request()

    first = get_guest_id(request)

    assert get_guest_id(request) == first
    assert request.session[GUEST_ID_SESSION_KEY] == str(first)


def test_each_session_gets_its_own_guest_id():
    assert get_guest_id(make_request()) != get_guest_id(make_request())


def test_a_signed_in_user_plays_as_their_player_id_in_every_session():
    player_id = uuid.uuid4()
    user = SimpleNamespace(is_authenticated=True, player_id=player_id)
    first, second = make_request(), make_request()
    first.user = second.user = user

    assert get_guest_id(first) == get_guest_id(second) == player_id


def test_an_anonymous_user_plays_as_the_session_guest():
    request = make_request()
    request.user = AnonymousUser()

    assert get_guest_id(request) == uuid.UUID(request.session[GUEST_ID_SESSION_KEY])
