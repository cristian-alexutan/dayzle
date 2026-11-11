"""API routes for the accounts app."""

from django.urls import path

from . import views

urlpatterns = [
    path("me/", views.me, name="accounts-me"),
    path("google/", views.google_login, name="accounts-google-login"),
    path("logout/", views.logout, name="accounts-logout"),
]
