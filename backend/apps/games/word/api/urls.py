"""API routes for the Word game app."""

from django.urls import path

from . import views

urlpatterns = [
    path("<game_day:day>/", views.game, name="word-game"),
    path("<game_day:day>/guess/", views.guess, name="word-guess"),
    path("<game_day:day>/hint/", views.hint, name="word-hint"),
]
