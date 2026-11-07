"""Django admin registration for the Math game app."""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from . import services
from .exceptions import GenerationFailedError, InvalidNumbersError
from .models import DIFFICULTY_CHOICES, MathPuzzle
from .rules import Difficulty
from .selectors import has_players

GAME_FIELDS = ("daily_puzzle", "target", "numbers")


class NumbersField(forms.CharField):
    """The starting numbers typed as a comma-separated list, e.g. ``25, 50, 3, 7, 7, 10``."""

    def prepare_value(self, value):
        if isinstance(value, list):
            return ", ".join(str(number) for number in value)
        return value

    def to_python(self, value) -> list[int] | None:
        value = super().to_python(value).strip()
        if not value:
            return None
        try:
            return [int(part) for part in value.split(",")]
        except ValueError:
            raise ValidationError("Enter whole numbers separated by commas.") from None


class MathPuzzleForm(forms.ModelForm):
    """Enter a target and 6 numbers, or leave both empty and pick a difficulty to generate them.

    Either way the solver checks the puzzle has an exact solution and fills in the difficulty,
    the minimum number of operations and an example solution.
    """

    numbers = NumbersField(required=False, help_text="6 numbers, e.g. 25, 50, 3, 7, 7, 10")
    generate = forms.ChoiceField(
        choices=[("", "---------"), *DIFFICULTY_CHOICES],
        required=False,
        label="Generate for difficulty",
        help_text="Leave the target and numbers empty to fill them with a random puzzle.",
    )

    class Meta:
        model = MathPuzzle
        fields = ["daily_puzzle", "target", "numbers"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target"].required = False
        self.content: services.PuzzleContent | None = None

    def clean(self):
        cleaned = super().clean()
        if self.errors:
            return cleaned
        target, numbers, difficulty = cleaned["target"], cleaned["numbers"], cleaned["generate"]
        # A started puzzle never gets this form (see MathPuzzleAdmin), but the chosen day can
        # still have players, e.g. when a puzzle is added or moved onto it.
        if has_players(cleaned["daily_puzzle"]):
            raise ValidationError(
                {"daily_puzzle": "Players have already started this day, so its puzzle is fixed."}
            )
        try:
            if target is None and numbers is None:
                if not difficulty:
                    raise ValidationError(
                        "Enter a target and 6 numbers, or pick a difficulty to generate them."
                    )
                self.content = services.generate_puzzle(Difficulty(difficulty))
            elif difficulty:
                raise ValidationError("Clear the target and numbers to generate a puzzle.")
            elif target is None or numbers is None:
                raise ValidationError("Enter both the target and the 6 numbers.")
            else:
                self.content = services.prepare_puzzle(numbers, target)
        except (InvalidNumbersError, GenerationFailedError) as error:
            raise ValidationError(error.message) from None
        cleaned["target"] = self.content.target
        cleaned["numbers"] = self.content.numbers
        return cleaned

    def save(self, commit=True):
        self.content.apply_to(self.instance)
        return super().save(commit)


@admin.register(MathPuzzle)
class MathPuzzleAdmin(admin.ModelAdmin):
    form = MathPuzzleForm
    fields = [
        "daily_puzzle",
        "generate",
        "target",
        "numbers",
        "difficulty",
        "min_operations",
        "example_solution",
    ]
    readonly_fields = ["difficulty", "min_operations", "example_solution"]
    list_display = ["daily_puzzle", "target", "numbers", "difficulty", "min_operations"]
    list_select_related = ["daily_puzzle"]
    list_filter = ["difficulty"]
    ordering = ["-daily_puzzle__date"]

    # Once a player has opened a puzzle, their saved steps and score depend on its numbers, so
    # it can't be changed, moved or deleted. This is checked again on every request, so a page
    # opened before the first player can't change the puzzle either.
    def _is_locked(self, puzzle: MathPuzzle | None) -> bool:
        return puzzle is not None and has_players(puzzle.daily_puzzle)

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if self._is_locked(obj):
            return [field for field in fields if field != "generate"]
        return fields

    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        if self._is_locked(obj):
            return [*GAME_FIELDS, *readonly]
        return readonly

    def get_form(self, request, obj=None, **kwargs):
        if self._is_locked(obj):
            kwargs["form"] = forms.ModelForm  # every field is read-only: nothing to check or save
        return super().get_form(request, obj, **kwargs)

    def has_delete_permission(self, request, obj=None):
        if self._is_locked(obj):
            return False
        return super().has_delete_permission(request, obj)

    @admin.display(description="Example solution")
    def example_solution(self, puzzle: MathPuzzle) -> str:
        return "; ".join(
            f"{step['left']} {step['op']} {step['right']} = {step['result']}"
            for step in puzzle.solution
        )
