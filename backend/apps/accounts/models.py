"""Database models for the accounts app."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model, defined early so login can be added later without a data migration."""

    # The player identity games use while this user is signed in (see
    # ``apps.common.players.get_guest_id``). It is the same in every session and on every
    # device, so a game finished once can't be played again after signing out and back in.
    player_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
