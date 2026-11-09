import factory
from django.utils import timezone

from apps.games.geo.models import GeoPuzzle, GeoPuzzleLocation, Location, Region
from apps.puzzles.models import Game
from apps.puzzles.tests.factories import DailyPuzzleFactory

# Cluj-Napoca comes from the data migration, so it exists in every test database.
CLUJ = "cluj-napoca"


def cluj() -> Region:
    return Region.objects.get(key=CLUJ)


class RegionFactory(factory.django.DjangoModelFactory):
    """A second region (around Oradea), for the region tests."""

    class Meta:
        model = Region

    key = factory.Sequence(lambda n: f"region-{n}")
    name = factory.Sequence(lambda n: f"Region {n}")
    south, west, north, east = 47.02, 21.88, 47.10, 21.98


class LocationFactory(factory.django.DjangoModelFactory):
    """A Cluj location on a grid about 1.2 km apart, so any 5 of them are spaced enough.

    A tiny shift per location makes every coordinate unique, so tests can look for it.
    """

    class Meta:
        model = Location

    region = factory.LazyFunction(cluj)
    panorama_id = factory.Sequence(lambda n: f"pano-{n}")
    latitude = factory.Sequence(lambda n: 46.74 + (n % 5) * 0.012 + n * 1e-6)
    longitude = factory.Sequence(lambda n: 23.54 + (n // 5 % 8) * 0.016 + n * 1e-6)
    last_checked_at = factory.LazyFunction(timezone.now)


class GeoPuzzleFactory(factory.django.DjangoModelFactory):
    """Today's Cluj game with 5 locations (pass ``locations`` to choose them)."""

    class Meta:
        model = GeoPuzzle
        skip_postgeneration_save = True

    daily_puzzle = factory.SubFactory(DailyPuzzleFactory, game=Game.GEO)
    region = factory.LazyFunction(cluj)
    score_scale_m = factory.LazyAttribute(lambda puzzle: puzzle.region.score_scale_m)

    @factory.post_generation
    def locations(self, create, extracted, **kwargs):
        locations = extracted or LocationFactory.create_batch(5, region=self.region)
        for position, location in enumerate(locations, start=1):
            GeoPuzzleLocation.objects.create(puzzle=self, location=location, position=position)
