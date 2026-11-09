"""Load the Trivia game's question bank from a JSON file."""

from pathlib import Path

from django.core.management.base import BaseCommand

from apps.games.trivia.services import QUESTIONS_FILE, import_question_file


class Command(BaseCommand):
    help = "Import trivia questions from a JSON file. Safe to run again."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=Path, default=QUESTIONS_FILE)

    def handle(self, *args, file: Path, **options):
        report = import_question_file(file)
        self.stdout.write(f"Added {report.added} question(s).")
        if report.skipped:
            self.stderr.write(f"Skipped {len(report.skipped)} invalid question(s):")
            for line in report.skipped:
                self.stderr.write(f"  {line}")
