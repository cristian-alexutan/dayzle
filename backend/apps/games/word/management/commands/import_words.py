"""Load the Word game's word lists (valid guesses and answers) into the word bank."""

from pathlib import Path

from django.core.management.base import BaseCommand

from apps.games.word.services import ANSWERS_FILE, GUESSES_FILE, import_word_files


class Command(BaseCommand):
    help = "Import the Word game's guess and answer lists. Safe to run again."

    def add_arguments(self, parser):
        parser.add_argument("--guesses", type=Path, default=GUESSES_FILE)
        parser.add_argument("--answers", type=Path, default=ANSWERS_FILE)

    def handle(self, *args, guesses: Path, answers: Path, **options):
        report = import_word_files(guesses, answers)
        self.stdout.write(f"Added {report.added} word(s); {report.answers} answer(s) in the list.")
        if report.skipped:
            listed = ", ".join(report.skipped[:10])
            self.stderr.write(f"Skipped {len(report.skipped)} invalid line(s): {listed}")
