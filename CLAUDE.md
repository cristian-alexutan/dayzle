# CLAUDE.md

Dayzle: a web platform with five daily puzzle games (Romanian Wordle, a Queens-style logic game,
a "Make the Target" math game, a 5-question trivia quiz, a GeoGuesser for Cluj-Napoca).

- `backend/`: REST API. Python 3.14, Django 6.1, Django REST Framework, PostgreSQL 16,
  drf-spectacular.
- `frontend/`: Vue 3 SPA. Vite, TypeScript, Vue Router, Pinia, TanStack Query, PrimeVue (Aura
  theme), Leaflet, vue-i18n. Node 24, npm, exact pins.

## MVP scope

The first demo is the five games only; README "MVP scope" lists the decisions. Key points:
everyone is anonymous (`guest_id` in the Django session, play-once per guest); puzzles are
hand-authored in Django admin as a `DailyPuzzle(game, date)` calendar row plus a per-game
content model; only today's puzzle is playable; one `GameResult` per player and puzzle holds
progress and the final `score` (higher is better) and server-measured `duration_ms`. Login,
subscriptions, archive, leaderboards, stats and friends are deferred: don't build them unless
asked. A custom `accounts.User` exists but is unused.

## Git commits

- Never add Claude as a co-author in commit messages (no `Co-Authored-By: Claude ...` trailer or any other AI attribution).

## Running things

Everything runs through Docker Compose from the repo root (a local `.env` copied from
`.env.example` is required). Run backend tools inside the container, not on the host: the host
Python is 3.12, which doesn't match the project's 3.14.

```bash
docker compose up --build -d
docker compose exec backend python manage.py migrate
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
```

CI (`.github/workflows/backend.yml`) runs ruff check, ruff format --check, migrate and pytest
against a Postgres service.

## Dependencies

Managed with pip-tools. Edit `backend/requirements/base.in` (runtime) or `dev.in` (dev/test),
then recompile inside the container so pins resolve for Python 3.14:

```bash
docker compose run --rm backend pip-compile --strip-extras requirements/base.in
docker compose run --rm backend pip-compile --strip-extras requirements/dev.in
```

Never edit the `.txt` files by hand. Commit `.in` and `.txt` together.

## Settings

`backend/config/settings/{base,dev,prod}.py`, selected via `DJANGO_SETTINGS_MODULE`. All
configuration comes from environment variables via django-environ (`DATABASE_URL`,
`DJANGO_SECRET_KEY`, ...). `TIME_ZONE = "Europe/Bucharest"`, `USE_TZ = True`.

## Architecture: modular monolith

Apps live in `backend/apps/`: `common`, `accounts`, `social`, `puzzles`, `results`,
`games/{word,logic,math,trivia,geo}`, `leaderboards`, `stats`, `subscriptions`. App labels for
games are prefixed (`games_word`, `games_math`, ...).

Every app uses the same layout:

- `models.py`: database models
- `services.py`: write operations and business rules
- `selectors.py`: read queries
- `api/serializers.py`, `api/views.py`, `api/urls.py`
- `tests/`

Each app's `api/urls.py` is mounted by `config/urls.py` under `/api/v1/<app>/` (games under
`/api/v1/games/<game>/`). OpenAPI is served at `/api/schema/` and `/api/docs/`.

### Shared building blocks for games

- `common`: `today_in_romania()` (only source of the game day), `get_guest_id(request)`,
  `DomainError` + `exception_handler` (errors as `{"error": {"code", "message", "details"}}`),
  `TimeStampedModel`.
- `puzzles`: `DailyPuzzle`, `register_game(...)` in each game's `AppConfig.ready()`,
  `get_playable_puzzle(game, day)`, the `<game_day:day>` URL converter (`today` or ISO date),
  `manage.py seed_dev` (DEBUG only; admin/admin).
- `results`: `GameResult`, `start_or_resume`, `save_progress`, `complete` (`AlreadyPlayedError`).
- Frontend: `http` / `ApiError` in `src/api/http.ts`, `mountWithPlugins` in `src/tests/utils.ts`.
- Step-by-step for a new game: CONTRIBUTING "How to build a game".

### Dependency direction (enforced in review, not by tooling)

- `games/*` depend on `puzzles` and `results`, never on each other.
- `leaderboards` and `stats` only read from `results`.
- `common` imports from no other app.
- No circular imports.

## Code style

- ruff with line length 100, target py314; rules E, W, F, I, B, UP, DJ. Migrations are excluded.
- Tests use pytest + pytest-django; put them in each app's `tests/` package.

## Frontend

Run frontend tools in the `frontend` compose service (`docker compose exec frontend npm run lint`)
or in a `node:24-alpine` container: the host Node is 18, which is too old.

- Scripts: `dev`, `build`, `preview`, `test`, `lint`, `format`, `type-check`, `generate:api`.
- TypeScript stays on 5.x: TypeScript 7 has no JS API, which `vue-tsc`, `typescript-eslint` and
  `openapi-typescript` need.
- Feature-based layout in `frontend/src/`: `app/`, `api/` (only place that talks to the backend),
  `shared/`, `features/<name>/` (public entry `index.ts`), `locales/`, `tests/`.
- `eslint-plugin-boundaries` (v7 policy API) forbids cross-feature imports, deep imports into a
  feature from outside, and shared/api importing features. Components and views may not import
  `@/api`. Full rules in the root `CONTRIBUTING.md`.
- `src/api/generated/schema.d.ts` is generated by `npm run generate:api` and committed. Inside
  compose, pass `API_SCHEMA_URL=http://backend:8000/api/schema/`.
- All user-facing strings go through vue-i18n (`ro` is the default locale).

## Docs and workflow

- There is a single `README.md` and a single `CONTRIBUTING.md`, both in the repo root, covering
  backend and frontend. Don't add per-folder READMEs.
- `main` is protected (ruleset `protect-main`): work on a branch and open a PR. PRs need one
  approval from a teammate and passing `test` (Backend CI) and `check` (Frontend CI).
- PRs are squash-merged only (repository setting), so the PR title becomes the commit message.
