"""Django admin registration for the Trivia game app."""

from django import forms
from django.contrib import admin, messages

from . import rules
from .models import Choice, Question, TriviaPuzzle, TriviaPuzzleQuestion
from .selectors import last_used_dates, other_days_with_questions


class ChoiceFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        kept = [
            form.cleaned_data
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE")
        ]
        if sum(1 for data in kept if data.get("is_correct")) != 1:
            raise forms.ValidationError("Mark exactly one choice as correct.")
        texts = [data.get("text", "").strip().lower() for data in kept]
        if len(set(texts)) != len(texts):
            raise forms.ValidationError("The choices must be different.")


class ChoiceInline(admin.TabularInline):
    model = Choice
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


class QuizQuestionFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        kept = [
            form.cleaned_data
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE")
        ]
        positions = sorted(data["position"] for data in kept if data.get("position"))
        if positions != list(range(1, rules.QUESTIONS_PER_QUIZ + 1)):
            raise forms.ValidationError(
                f"Use each position from 1 to {rules.QUESTIONS_PER_QUIZ} exactly once."
            )
        questions = [data["question"] for data in kept if data.get("question")]
        if len(set(questions)) != len(questions):
            raise forms.ValidationError("A question can appear only once in a quiz.")


class QuizQuestionInline(admin.TabularInline):
    model = TriviaPuzzleQuestion
    formset = QuizQuestionFormSet
    extra = 0
    min_num = max_num = rules.QUESTIONS_PER_QUIZ
    validate_min = validate_max = True
    autocomplete_fields = ["question"]


@admin.register(TriviaPuzzle)
class TriviaPuzzleAdmin(admin.ModelAdmin):
    list_display = ["daily_puzzle"]
    list_select_related = ["daily_puzzle"]
    ordering = ["-daily_puzzle__date"]
    inlines = [QuizQuestionInline]

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
