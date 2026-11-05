import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

CSRF_TOKEN = "a" * 32


def test_logged_in_admin_can_post_through_the_frontend_dev_server(admin_user):
    # Cookies are shared across ports on localhost, so an admin login reaches the game too. The
    # Vite proxy sends the backend's Host with the frontend's Origin.
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(admin_user)
    client.cookies["csrftoken"] = CSRF_TOKEN

    response = client.post(
        "/api/v1/results/word/today/heartbeat/",
        headers={"Host": "localhost:8000", "Origin": "http://localhost:5173"},
        HTTP_X_CSRFTOKEN=CSRF_TOKEN,
    )

    # No puzzle exists in this test: getting past CSRF is what matters, not a 403.
    assert response.status_code == 404
    assert response.data["error"]["code"] == "no_puzzle"
