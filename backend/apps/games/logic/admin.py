"""Django admin registration for the Logic game app."""

from django.contrib import admin

from .models import LogicPuzzle


@admin.register(LogicPuzzle)
class LogicPuzzleAdmin(admin.ModelAdmin):
    list_display = ["daily_puzzle", "size"]
    list_select_related = ["daily_puzzle"]
    ordering = ["-daily_puzzle__date"]
