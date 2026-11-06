"""API routes for the Logic game app."""

from django.urls import path

from . import views

urlpatterns = [
    path("<game_day:day>/", views.game, name="logic-game"),
    path("<game_day:day>/place/", views.place, name="logic-place"),
    path("<game_day:day>/marks/", views.marks, name="logic-marks"),
]
