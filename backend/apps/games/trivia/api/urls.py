"""API routes for the Trivia game app."""

from django.urls import path

from . import views

urlpatterns = [
    path("<game_day:day>/", views.game, name="trivia-game"),
    path("<game_day:day>/answer/", views.answer, name="trivia-answer"),
]
