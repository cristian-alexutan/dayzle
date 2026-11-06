"""Django admin registration for the Trivia game app."""

from django import forms
from django.contrib import admin, messages
from django.db import transaction

from . import rules
from .models import Choice, Question, TriviaPuzzle, TriviaPuzzleQuestion
from .selectors import has_players, last_used_dates, other_days_with_questions


class RowCheckedByFormSetForm(forms.ModelForm):
    """An inline row whose unique fields are checked by its formset, not against the database.

    Checking one row against the rows already saved would reject a swap (two rows exchanging
    a position, a question or the correct tick), because each row clashes with the other's
    old value. The formset checks the submitted rows together instead, and the admin saves
    them in an order the database accepts.
    """

    def clean(self):
        cleaned_data = super().clean()
        self._validate_unique = False
        self._validate_constraints = False
        return cleaned_data


def _kept_rows(formset: forms.BaseInlineFormSet) -> list[dict]:
    return [
        form.cleaned_data
        for form in formset.forms
        if form.cleaned_data and not form.cleaned_data.get("DELETE")
    ]


class ChoiceFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        kept = _kept_rows(self)
        if sum(1 for data in kept if data.get("is_correct")) != 1:
            raise forms.ValidationError("Mark exactly one choice as correct.")
        texts = [data.get("text", "").strip().lower() for data in kept]
        if len(set(texts)) != len(texts):
            raise forms.ValidationError("The choices must be different.")


class ChoiceInline(admin.TabularInline):
    model = Choice
    form = RowCheckedByFormSetForm
    formset = ChoiceFormSet
    extra = 0
    min_num = max_num = rules.CHOICES_PER_QUESTION
    validate_min = validate_max = True
    can_delete = False


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "category", "difficulty", "last_used"]
    list_filter = ["category", "difficulty"]
    search_fields = ["text"]
    inlines = [ChoiceInline]

    def get_queryset(self, request):
        return last_used_dates()

    @admin.display(ordering="last_used", description="Last used")
    def last_used(self, obj):
        return obj.last_used

    def save_formset(self, request, form, formset, change):
        if formset.model is not Choice:
            return super().save_formset(request, form, formset, change)
        choices = formset.save(commit=False)
        # Only one choice may be correct in the database at any moment, so untick the old
        # correct choice before ticking the new one.
        with transaction.atomic():
            for choice in sorted(choices, key=lambda choice: choice.is_correct):
                choice.save()
        formset.save_m2m()


class QuizQuestionFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        kept = _kept_rows(self)
        positions = sorted(data["position"] for data in kept if data.get("position"))
        if positions != list(range(1, rules.QUESTIONS_PER_QUIZ + 1)):
            raise forms.ValidationError(
                f"Use each position from 1 to {rules.QUESTIONS_PER_QUIZ} exactly once."
            )
        questions = [data["question"] for data in kept if data.get("question")]
        if len(set(questions)) != len(questions):
            raise forms.ValidationError("A question can appear only once in a quiz.")


class LockedOncePlayedMixin:
    """Read-only once players have opened the quiz: their progress follows its questions."""

    def _locked(self, obj) -> bool:
        return obj is not None and obj.pk is not None and has_players(obj)

    def has_change_permission(self, request, obj=None):
        return not self._locked(obj) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return not self._locked(obj) and super().has_delete_permission(request, obj)


class QuizQuestionInline(LockedOncePlayedMixin, admin.TabularInline):
    model = TriviaPuzzleQuestion
    form = RowCheckedByFormSetForm
    formset = QuizQuestionFormSet
    extra = 0
    min_num = max_num = rules.QUESTIONS_PER_QUIZ
    validate_min = validate_max = True
    can_delete = False
    autocomplete_fields = ["question"]

    def has_add_permission(self, request, obj=None):
        return not self._locked(obj) and super().has_add_permission(request, obj)


@admin.register(TriviaPuzzle)
class TriviaPuzzleAdmin(LockedOncePlayedMixin, admin.ModelAdmin):
    list_display = ["daily_puzzle"]
    list_select_related = ["daily_puzzle"]
    ordering = ["-daily_puzzle__date"]
    inlines = [QuizQuestionInline]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        quiz = self.get_object(request, object_id)
        if request.method == "GET" and self._locked(quiz):
            self.message_user(
                request,
                "Players have already started this quiz, so its questions can't be changed.",
                level=messages.WARNING,
            )
        return super().change_view(request, object_id, form_url, extra_context)

    def save_formset(self, request, form, formset, change):
        if formset.model is not TriviaPuzzleQuestion:
            return super().save_formset(request, form, formset, change)
        entries = formset.save(commit=False)
        # A row's new position or question may still belong to another row, as in a swap.
        # Remove the changed rows first and insert them again (same ids) with their new values.
        with transaction.atomic():
            changed = [entry.pk for entry in entries if entry.pk is not None]
            TriviaPuzzleQuestion.objects.filter(pk__in=changed).delete()
            for entry in entries:
                entry.save(force_insert=True)
        formset.save_m2m()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        quiz = form.instance
        categories = set(quiz.questions.values_list("category", flat=True))
        if len(categories) < rules.MIN_CATEGORIES:
            self.message_user(
                request,
                f"The quiz covers only {len(categories)} categories; "
                f"aim for at least {rules.MIN_CATEGORIES}.",
                level=messages.WARNING,
            )
        for text, days in other_days_with_questions(quiz).items():
            listed = ", ".join(day.isoformat() for day in days)
            self.message_user(
                request, f"“{text}” is also used on: {listed}", level=messages.WARNING
            )
