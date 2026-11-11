import uuid

from django.db import migrations, models


def give_every_user_a_player_id(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.filter(player_id__isnull=True):
        user.player_id = uuid.uuid4()
        user.save(update_fields=["player_id"])


def move_results_to_player_ids(apps, schema_editor):
    """Results already linked to a user are looked up by its player_id from now on."""
    User = apps.get_model("accounts", "User")
    GameResult = apps.get_model("results", "GameResult")
    for user in User.objects.all():
        GameResult.objects.filter(user=user).update(guest_id=user.player_id)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("results", "0002_active_play_time"),
    ]

    operations = [
        # Added in three steps, so existing users get different ids rather than one shared default.
        migrations.AddField(
            model_name="user",
            name="player_id",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(give_every_user_a_player_id, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="player_id",
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False),
        ),
        migrations.RunPython(move_results_to_player_ids, migrations.RunPython.noop),
    ]
