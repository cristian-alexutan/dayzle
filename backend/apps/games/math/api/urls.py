"""API routes for the Math game app."""

from django.urls import path

from . import views

urlpatterns = [
    path("<game_day:day>/", views.game, name="math-game"),
    path("<game_day:day>/progress/", views.progress, name="math-progress"),
    path("<game_day:day>/submit/", views.submit, name="math-submit"),
]
