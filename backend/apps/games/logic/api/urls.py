"""API routes for the Logic game app."""

from django.urls import path

from . import views

urlpatterns = [
    path("<game_day:day>/", views.game, name="logic-game"),
    path("<game_day:day>/cell/", views.cell, name="logic-cell"),
    path("<game_day:day>/clear/", views.clear, name="logic-clear"),
]
