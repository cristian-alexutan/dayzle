"""API routes for the GeoGuesser game app."""

from django.urls import path

from . import views

urlpatterns = [
    path("regions/", views.regions, name="geo-regions"),
    path("<game_day:day>/", views.game, name="geo-game"),
    path("<game_day:day>/guess/", views.guess, name="geo-guess"),
]
