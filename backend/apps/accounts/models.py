"""Database models for the accounts app."""

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model, defined early so login can be added later without a data migration."""
