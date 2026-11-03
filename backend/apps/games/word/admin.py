"""Django admin registration for the Word game app."""

from django.contrib import admin, messages

from .models import Word, WordPuzzle
from .selectors import other_days_with_answer


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ["text", "is_answer"]
    list_editable = ["is_answer"]
    list_filter = ["is_answer"]
    search_fields = ["text"]


@admin.register(WordPuzzle)
class WordPuzzleAdmin(admin.ModelAdmin):
    list_display = ["daily_puzzle", "answer"]
    list_select_related = ["daily_puzzle", "answer"]
    autocomplete_fields = ["answer"]
    ordering = ["-daily_puzzle__date"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        days = other_days_with_answer(obj)
        if days:
            listed = ", ".join(day.isoformat() for day in days)
            self.message_user(
                request, f"“{obj.answer}” is also the word of: {listed}", level=messages.WARNING
            )
