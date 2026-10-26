"""Database models for the results app."""

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.common.models import TimeStampedModel
from apps.puzzles.models import DailyPuzzle


class GameResult(TimeStampedModel):
    """One player's attempt at one daily puzzle, from start to finish.

    Shared by all games. Ranking uses ``score`` (higher is better) and then ``duration_ms``;
    anything game-specific goes in ``details``.
    """

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"

    daily_puzzle = models.ForeignKey(DailyPuzzle, on_delete=models.PROTECT, related_name="results")
    guest_id = models.UUIDField(null=True, blank=True)
    # Unused until login exists; results then belong to a user instead of a guest.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IN_PROGRESS)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    solved = models.BooleanField(default=False)
    score = models.IntegerField(default=0)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    is_archive = models.BooleanField(default=False)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(guest_id__isnull=False) | Q(user__isnull=False),
                name="result_has_player",
            ),
            models.UniqueConstraint(
                fields=["guest_id", "daily_puzzle"],
                condition=Q(guest_id__isnull=False),
                name="one_result_per_guest_per_puzzle",
            ),
            models.UniqueConstraint(
                fields=["user", "daily_puzzle"],
                condition=Q(user__isnull=False),
                name="one_result_per_user_per_puzzle",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.daily_puzzle} ({self.get_status_display()})"
