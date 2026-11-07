import random
import uuid
from datetime import timedelta

import factory
import pytest
from django.db import IntegrityError

from apps.common.time import today_in_romania
from apps.games.geo import rules, services, streetview
from apps.games.geo.exceptions import (
    AlreadyAnsweredError,
    InvalidGuessError,
    RegionLockedError,
    StreetViewError,
    TemporaryStreetViewError,
    UnknownRegionError,
)
from apps.games.geo.models import GeoPuzzle, Location
from apps.games.geo.selectors import pick_locations
from apps.puzzles.exceptions import ArchiveUnavailableError, NoPuzzleError
from apps.puzzles.models import DailyPuzzle, Game
from apps.puzzles.tests.factories import DailyPuzzleFactory
from apps.results.exceptions import AlreadyPlayedError
from apps.results.models import GameResult

from .factories import CLUJ, GeoPuzzleFactory, LocationFactory, RegionFactory, cluj

pytestmark = pytest.mark.django_db


@pytest.fixture
def guest():
    return uuid.uuid4()


@pytest.fixture
def bank():
    """Enough spaced Cluj locations for several days."""
    return LocationFactory.create_batch(20)


def today():
    return today_in_romania()


def play_round(guest, game, *, offset=0.0):
    """Guess the current round at its real spot, shifted north by ``offset`` degrees."""
    current = len(game.result.details["guesses"]) + 1
    location = game.locations[current - 1]
    return services.guess(
        guest, CLUJ, today(), current, location.latitude + offset, location.longitude
    )


# The daily game


def test_first_open_makes_today_game_from_the_bank(guest, bank):
    game = services.open_game(guest, CLUJ, today())

    assert game.puzzle.daily_puzzle.game == Game.GEO
    assert game.puzzle.daily_puzzle.date == today()
    assert len(game.locations) == rules.ROUNDS
    assert rules.is_spaced([location.point for location in game.locations], 1000)


def test_everyone_gets_the_same_game(bank):
    first = services.open_game(uuid.uuid4(), CLUJ, today())
    second = services.open_game(uuid.uuid4(), CLUJ, today())

    assert first.puzzle.pk == second.puzzle.pk
    assert first.locations == second.locations
    assert GeoPuzzle.objects.count() == 1
    assert DailyPuzzle.objects.filter(game=Game.GEO).count() == 1


def test_no_region_means_the_default_region(guest, bank):
    assert services.open_game(guest, None, today()).puzzle.region.key == CLUJ


def test_a_game_made_by_a_simultaneous_request_is_reused(guest, bank, monkeypatch):
    winner = GeoPuzzleFactory(daily_puzzle=DailyPuzzleFactory(game=Game.GEO))
    real_lookup = services.get_geo_puzzle
    calls = []

    def lookup_after_losing_the_race(daily_puzzle, region):
        calls.append(1)
        # The first lookup misses, as if the other request hadn't committed yet.
        return None if len(calls) == 1 else real_lookup(daily_puzzle, region)

    def create_too_late(*args):
        raise IntegrityError("one_geo_puzzle_per_region_per_day")

    monkeypatch.setattr(services, "get_geo_puzzle", lookup_after_losing_the_race)
    monkeypatch.setattr(services, "_create_puzzle", create_too_late)

    assert services.open_game(guest, CLUJ, today()).puzzle.pk == winner.pk


def test_a_too_small_bank_means_no_puzzle(guest):
    LocationFactory.create_batch(rules.ROUNDS - 1)

    with pytest.raises(NoPuzzleError):
        services.open_game(guest, CLUJ, today())
    assert not GeoPuzzle.objects.exists()


def test_inactive_locations_are_never_picked(guest):
    LocationFactory.create_batch(rules.ROUNDS, is_active=False)

    with pytest.raises(NoPuzzleError):
        services.open_game(guest, CLUJ, today())


def test_past_days_are_archive_and_future_days_have_no_puzzle(guest, bank):
    with pytest.raises(ArchiveUnavailableError):
        services.open_game(guest, CLUJ, today() - timedelta(days=1))
    with pytest.raises(NoPuzzleError):
        services.open_game(guest, CLUJ, today() + timedelta(days=1))
    assert not DailyPuzzle.objects.filter(game=Game.GEO).exists()


def test_unknown_or_inactive_region(guest, bank):
    with pytest.raises(UnknownRegionError):
        services.open_game(guest, "atlantis", today())
    hidden = RegionFactory(is_active=False)
    with pytest.raises(UnknownRegionError):
        services.open_game(guest, hidden.key, today())


def test_pick_prefers_locations_not_used_yet():
    used = LocationFactory.create_batch(5)
    GeoPuzzleFactory(
        daily_puzzle=DailyPuzzleFactory(game=Game.GEO, date=today() - timedelta(days=1)),
        locations=used,
    )
    fresh = LocationFactory.create_batch(5)

    assert set(pick_locations(cluj(), random.Random(1))) == set(fresh)


def test_pick_keeps_the_spacing():
    # Two locations 100 m apart can't both be in one game.
    LocationFactory(latitude=46.770, longitude=23.590)
    LocationFactory(latitude=46.7709, longitude=23.590)

    picked = pick_locations(cluj(), random.Random(1))

    assert len(picked) == 1


# Playing


def test_opening_starts_the_result_in_the_region(guest, bank):
    game = services.open_game(guest, CLUJ, today())

    assert game.result.status == GameResult.Status.IN_PROGRESS
    assert game.result.details == {"region": CLUJ, "guesses": []}


def test_another_region_the_same_day_is_refused(guest, bank):
    other = RegionFactory()
    services.open_game(guest, CLUJ, today())

    with pytest.raises(RegionLockedError) as raised:
        services.open_game(guest, other.key, today())
    assert raised.value.details == {"region": CLUJ}
    # The other region's game isn't even made for this player.
    assert not GeoPuzzle.objects.filter(region=other).exists()


def test_a_player_can_open_another_region_if_the_first_had_no_game(guest):
    other = RegionFactory()
    with pytest.raises(NoPuzzleError):
        services.open_game(guest, CLUJ, today())  # Cluj has no locations yet
    LocationFactory.create_batch(
        5,
        region=other,
        latitude=factory.Iterator([47.03, 47.045, 47.06, 47.075, 47.09]),
        longitude=21.93,
    )

    assert services.open_game(guest, other.key, today()).puzzle.region == other


def test_a_spot_on_guess_scores_1000_and_reveals_nothing_else(guest, bank):
    game = services.open_game(guest, CLUJ, today())

    game = play_round(guest, game)

    [given] = game.result.details["guesses"]
    assert given["round"] == 1
    assert given["distance_m"] == 0
    assert given["score"] == 1000
    assert game.result.status == GameResult.Status.IN_PROGRESS


def test_a_guess_one_km_off_scores_with_the_region_scale(guest, bank):
    game = services.open_game(guest, CLUJ, today())

    # 0.009° of latitude is about 1001 m.
    game = play_round(guest, game, offset=0.009)

    given = game.result.details["guesses"][0]
    assert given["distance_m"] == 1001
    assert given["score"] == rules.round_score(1001, 1500) == 513


def test_rounds_are_guessed_in_order_and_once(guest, bank):
    game = services.open_game(guest, CLUJ, today())
    location = game.locations[0]

    with pytest.raises(InvalidGuessError) as raised:
        services.guess(guest, CLUJ, today(), 2, location.latitude, location.longitude)
    assert raised.value.details == {"current_round": 1}

    play_round(guest, game)
    with pytest.raises(AlreadyAnsweredError):
        services.guess(guest, CLUJ, today(), 1, location.latitude, location.longitude)


def test_a_guess_outside_the_region_doesnt_use_the_round(guest, bank):
    services.open_game(guest, CLUJ, today())

    with pytest.raises(InvalidGuessError):
        services.guess(guest, CLUJ, today(), 1, 44.43, 26.10)  # Bucharest

    result = GameResult.objects.get(guest_id=guest)
    assert result.details["guesses"] == []


def test_a_guess_before_opening_opens_the_game(guest, bank):
    game = services.guess(guest, CLUJ, today(), 1, 46.77, 23.59)

    assert len(game.result.details["guesses"]) == 1


def test_the_fifth_guess_finishes_the_game(guest, bank):
    game = services.open_game(guest, CLUJ, today())
    for _ in range(4):
        game = play_round(guest, game)
    game = play_round(guest, game, offset=0.009)

    result = game.result
    assert result.status == GameResult.Status.COMPLETED
    assert result.score == 4 * 1000 + 513
    assert result.solved
    assert result.duration_ms is not None


def test_a_low_total_is_not_solved(guest, bank):
    game = services.open_game(guest, CLUJ, today())
    for _ in range(5):
        game = play_round(guest, game, offset=0.015)  # about 1.7 km off: 329 points

    assert game.result.status == GameResult.Status.COMPLETED
    assert not game.result.solved


def test_a_finished_game_cant_be_played_again(guest, bank):
    game = services.open_game(guest, CLUJ, today())
    for _ in range(5):
        game = play_round(guest, game)

    # Even an otherwise invalid guess reports the finished game first.
    with pytest.raises(AlreadyPlayedError):
        services.guess(guest, CLUJ, today(), 1, 44.43, 26.10)
    assert services.open_game(guest, CLUJ, today()).result.status == "completed"


# The location bank


def fake_find(monkeypatch, panoramas):
    """Make find_panorama return these panoramas one per call (None once they run out)."""
    queue = list(panoramas)
    monkeypatch.setattr(streetview, "find_panorama", lambda *args: queue.pop(0) if queue else None)


def test_generate_adds_google_panoramas_inside_the_region(monkeypatch):
    fake_find(
        monkeypatch,
        [
            streetview.Panorama("a", 46.77, 23.59),
            None,
            streetview.Panorama("b", 44.43, 26.10),  # outside Cluj
            streetview.Panorama("a", 46.77, 23.59),  # already in the bank
            streetview.Panorama("c", 46.76, 23.60),
        ],
    )

    report = services.generate_locations(cluj(), 2, random.Random(1))

    assert report.added == 2
    assert report.attempts == 5
    assert set(Location.objects.values_list("panorama_id", flat=True)) == {"a", "c"}
    assert Location.objects.get(panorama_id="c").latitude == 46.76


def test_generate_gives_up_after_too_many_tries(monkeypatch):
    fake_find(monkeypatch, [])

    report = services.generate_locations(cluj(), 3, random.Random(1))

    assert report.added == 0
    assert report.attempts == 3 * services.ATTEMPTS_PER_LOCATION


def fake_find_with_errors(monkeypatch, answers):
    """Like fake_find, but an exception class in ``answers`` is raised for that call."""
    queue = list(answers)

    def find(*args):
        answer = queue.pop(0) if queue else None
        if isinstance(answer, type) and issubclass(answer, Exception):
            raise answer("Street View returned UNKNOWN_ERROR: no details")
        return answer

    monkeypatch.setattr(streetview, "find_panorama", find)


def test_generate_keeps_going_after_a_temporary_google_error(monkeypatch):
    fake_find_with_errors(
        monkeypatch,
        [
            streetview.Panorama("a", 46.77, 23.59),
            TemporaryStreetViewError,
            streetview.Panorama("b", 46.76, 23.60),
        ],
    )

    report = services.generate_locations(cluj(), 2, random.Random(1))

    assert (report.added, report.attempts, report.errors) == (2, 3, 1)


def test_generate_stops_after_too_many_temporary_errors_in_a_row(monkeypatch):
    fake_find_with_errors(
        monkeypatch,
        [
            streetview.Panorama("a", 46.77, 23.59),
            *[TemporaryStreetViewError] * services.MAX_TEMPORARY_ERRORS_IN_A_ROW,
        ],
    )

    with pytest.raises(TemporaryStreetViewError):
        services.generate_locations(cluj(), 5, random.Random(1))
    # The location found before the errors is kept.
    assert list(Location.objects.values_list("panorama_id", flat=True)) == ["a"]


def test_generate_stops_at_once_on_a_refused_key(monkeypatch):
    fake_find_with_errors(monkeypatch, [StreetViewError])

    with pytest.raises(StreetViewError):
        services.generate_locations(cluj(), 5, random.Random(1))


def test_seed_survives_google_failing(monkeypatch):
    fake_find_with_errors(monkeypatch, [TemporaryStreetViewError] * 10)
    day = DailyPuzzleFactory(game=Game.GEO)

    services.seed_puzzle(day)  # logs a warning instead of raising

    assert not GeoPuzzle.objects.exists()


def test_recheck_refreshes_coordinates_and_deactivates_removed_panoramas(monkeypatch):
    kept, removed = LocationFactory(), LocationFactory()
    answers = {kept.panorama_id: streetview.Panorama(kept.panorama_id, 46.7, 23.6)}
    monkeypatch.setattr(streetview, "get_panorama", answers.get)

    report = services.recheck_locations([kept, removed])

    kept.refresh_from_db()
    removed.refresh_from_db()
    assert report.checked == 2
    assert report.removed == [removed]
    assert (kept.latitude, kept.longitude, kept.is_active) == (46.7, 23.6, True)
    assert not removed.is_active


def test_seed_generates_a_bank_then_makes_the_day(monkeypatch):
    made = iter(LocationFactory.build_batch(services.SEED_BANK_SIZE))
    fake_find(
        monkeypatch,
        [streetview.Panorama(loc.panorama_id, loc.latitude, loc.longitude) for loc in made],
    )
    day = DailyPuzzleFactory(game=Game.GEO)

    services.seed_puzzle(day)

    assert Location.objects.count() == services.SEED_BANK_SIZE
    assert GeoPuzzle.objects.get(daily_puzzle=day).entries.count() == rules.ROUNDS


def test_seed_without_a_key_skips_an_empty_region(settings):
    settings.GOOGLE_MAPS_SERVER_KEY = ""
    day = DailyPuzzleFactory(game=Game.GEO)

    services.seed_puzzle(day)

    assert not GeoPuzzle.objects.exists()


def test_seed_without_a_key_uses_an_existing_bank(settings, bank):
    settings.GOOGLE_MAPS_SERVER_KEY = ""
    day = DailyPuzzleFactory(game=Game.GEO)

    services.seed_puzzle(day)

    assert GeoPuzzle.objects.filter(daily_puzzle=day).exists()
