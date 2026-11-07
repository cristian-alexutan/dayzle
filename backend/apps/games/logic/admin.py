"""Django admin registration for the Logic game app."""

from django.contrib import admin

from .models import LogicPuzzle

CONTENT_FIELDS = ["daily_puzzle", "size", "regions", "solution"]


@admin.register(LogicPuzzle)
class LogicPuzzleAdmin(admin.ModelAdmin):
    list_display = ["daily_puzzle", "size"]
    list_select_related = ["daily_puzzle"]
    ordering = ["-daily_puzzle__date"]

    # Once players have started a puzzle, changing or deleting it would break their games.
    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.has_been_played():
            return CONTENT_FIELDS
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.has_been_played():
            return False
        return super().has_delete_permission(request, obj)
