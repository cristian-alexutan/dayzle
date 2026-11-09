from django.db import migrations

# The built-up area of Cluj-Napoca, from Mănăștur to Someșeni and from Bulgaria to Bună Ziua.
CLUJ_NAPOCA = {
    "key": "cluj-napoca",
    "name": "Cluj-Napoca",
    "south": 46.735,
    "west": 23.53,
    "north": 46.805,
    "east": 23.67,
    "score_scale_m": 1500,
    "min_spacing_m": 1000,
    "is_default": True,
}


def add_cluj_napoca(apps, schema_editor):
    Region = apps.get_model("games_geo", "Region")
    Region.objects.update_or_create(key=CLUJ_NAPOCA["key"], defaults=CLUJ_NAPOCA)


class Migration(migrations.Migration):
    dependencies = [("games_geo", "0001_regions_and_locations")]

    operations = [migrations.RunPython(add_cluj_napoca, migrations.RunPython.noop)]
