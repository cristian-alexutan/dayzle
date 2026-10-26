"""Shared pytest fixtures."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    """API client that keeps its session (and so its guest id) between requests."""
    return APIClient()
