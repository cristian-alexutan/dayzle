import django.core.validators
from django.db import migrations, models


def copy_region_scale(apps, schema_editor):
    GeoPuzzle = apps.get_model("games_geo", "GeoPuzzle")
    for puzzle in GeoPuzzle.objects.select_related("region"):
        puzzle.score_scale_m = puzzle.region.score_scale_m
        puzzle.save(update_fields=["score_scale_m"])


class Migration(migrations.Migration):
    dependencies = [("games_geo", "0002_cluj_napoca")]

    operations = [
        migrations.AddField(
            model_name="geopuzzle",
            name="score_scale_m",
            field=models.PositiveIntegerField(
                default=1500, validators=[django.core.validators.MinValueValidator(1)]
            ),
            preserve_default=False,
        ),
        migrations.RunPython(copy_region_scale, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="region",
            name="score_scale_m",
            field=models.PositiveIntegerField(
                default=1500,
                help_text=(
                    "Used by games made after a change: each day's game keeps the scale it was "
                    "made with, so everyone that day is scored the same way."
                ),
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
    ]
