"""Django admin registration for the puzzles app."""

from django.contrib import admin, messages

from .models import DailyPuzzle
from .selectors import get_missing_days


@admin.register(DailyPuzzle)
class DailyPuzzleAdmin(admin.ModelAdmin):
    list_display = ["date", "game"]
    list_filter = ["game"]
    date_hierarchy = "date"

    def changelist_view(self, request, extra_context=None):
        for game, days in get_missing_days().items():
            listed = ", ".join(day.strftime("%d %b") for day in days)
            self.message_user(
                request, f"No {game} puzzle scheduled for: {listed}", level=messages.WARNING
            )
        return super().changelist_view(request, extra_context)
