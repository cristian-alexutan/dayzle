"""Database models for the common app."""

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model that records when a row was created and last updated."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
