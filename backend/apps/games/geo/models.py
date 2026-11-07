"""Database models for the GeoGuesser game app."""

from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import TimeStampedModel
from apps.puzzles.models import DailyPuzzle, Game

from . import rules


class Region(TimeStampedModel):
    """An area the game can be played in, such as a city. Players pick one for the day."""

    key = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=100)
    south = models.FloatField()
    west = models.FloatField()
    north = models.FloatField()
    east = models.FloatField()
    # The distance at which a round's score falls to about a third (see rules.round_score).
    score_scale_m = models.PositiveIntegerField(default=1500, validators=[MinValueValidator(1)])
    # A day's locations are at least this far apart from each other.
    min_spacing_m = models.PositiveIntegerField(default=1000)
    is_active = models.BooleanField(default=True)
    # The region played when the request names none. Exactly one region should have it.
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_default", "name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(south__lt=models.F("north"), west__lt=models.F("east")),
                name="region_bounds_not_empty",
            ),
            models.UniqueConstraint(
                fields=["is_default"],
                condition=models.Q(is_default=True),
                name="one_default_region",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def bounds(self) -> rules.Bounds:
        return rules.Bounds(south=self.south, west=self.west, north=self.north, east=self.east)


class Location(TimeStampedModel):
    """One Street View panorama in a region's location bank.

    Made by ``manage.py generate_locations``, never hand-picked. Google lets us keep the
    panorama ID indefinitely; the coordinates are a cache refreshed by ``check_panoramas``.
    """

    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="locations")
    panorama_id = models.CharField(max_length=128, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    is_active = models.BooleanField(default=True)
    last_checked_at = models.DateTimeField()

    class Meta:
        ordering = ["region", "id"]

    def __str__(self) -> str:
        return self.panorama_id

    @property
    def point(self) -> rules.Point:
        return rules.Point(self.latitude, self.longitude)


class GeoPuzzle(TimeStampedModel):
    """One region's daily game: its 5 locations, in order (see ``GeoPuzzleLocation``).

    Made automatically the first time someone opens the day, never authored by an admin.
    """

    daily_puzzle = models.ForeignKey(
        DailyPuzzle,
        on_delete=models.CASCADE,
        related_name="geo",
        limit_choices_to={"game": Game.GEO},
    )
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="puzzles")
    locations = models.ManyToManyField(
        Location, through="GeoPuzzleLocation", related_name="puzzles"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["daily_puzzle", "region"], name="one_geo_puzzle_per_region_per_day"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.daily_puzzle} ({self.region})"


class GeoPuzzleLocation(models.Model):
    """One location of a daily game and its round (1 to 5)."""

    puzzle = models.ForeignKey(GeoPuzzle, on_delete=models.CASCADE, related_name="entries")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="entries")
    position = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["puzzle", "position"], name="one_location_per_round"),
            models.UniqueConstraint(fields=["puzzle", "location"], name="no_repeated_location"),
        ]

    def __str__(self) -> str:
        return f"{self.position}. {self.location}"
