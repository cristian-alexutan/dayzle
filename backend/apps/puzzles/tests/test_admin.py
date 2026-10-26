import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_changelist_warns_about_unscheduled_days(admin_client, clean_registry):
    clean_registry.register_game(key="word", name="Word", content_model=object)

    response = admin_client.get(reverse("admin:puzzles_dailypuzzle_changelist"))

    assert response.status_code == 200
    warnings = [str(m) for m in get_messages(response.wsgi_request)]
    assert any(w.startswith("No word puzzle scheduled for:") for w in warnings)
