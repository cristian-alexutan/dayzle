"""API routes for the results app."""

from django.urls import path

from . import views

urlpatterns = [
    path("<str:game>/<game_day:day>/heartbeat/", views.heartbeat, name="results-heartbeat"),
]
