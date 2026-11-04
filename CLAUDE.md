# CLAUDE.md

Dayzle: a web platform with five daily puzzle games: Cuvântăl (a Romanian Wordle), a Queens-style
logic game, a "Make the Target" math game, a 5-question trivia quiz, a GeoGuesser for Cluj-Napoca.

- `backend/`: REST API. Python 3.14, Django 6.1, Django REST Framework, PostgreSQL 16,
  drf-spectacular.
- `frontend/`: Vue 3 SPA. Vite, TypeScript, Vue Router, Pinia, TanStack Query, PrimeVue (Aura
  theme), PrimeIcons, Leaflet, vue-i18n. Node 24, npm, exact pins.

## Status

- **Cuvântăl (`word`):** the demo part is built, backend and frontend. Archive, practice, streak,
  statistics, leaderboards and the share button are not.
- **`logic`, `math`, `trivia`, `geo`:** placeholders only (docstring-only backend files, one-line
  comment frontend files). So are `social`, `leaderboards`, `stats`, `subscriptions` and the
  frontend's `auth`, `archive`, `admin`, `social`, `stats`, `leaderboards`, `subscription`.
- `/` is intentionally blank: there is no home page or menu yet. The only route is `/games/word`.

## MVP scope

The first demo is the five games only; README "MVP scope" lists the decisions. Key points:
everyone is anonymous (`guest_id` in the Django session, play-once per guest); puzzles are
hand-authored in Django admin as a `DailyPuzzle(game, date)` calendar row plus a per-game
content model; only today's puzzle is playable; one `GameResult` per player and puzzle holds
progress and the final `score` (higher is better) and server-measured `duration_ms` (active
time only: heartbeats every 15 s while the game is visible, gaps capped at 30 s). Login,
subscriptions, archive, leaderboards, stats and friends are deferred: don't build them unless
asked. A custom `accounts.User` exists but is unused, except for Django admin logins.

## Git commits

- Never add AI attribution: no `Co-Authored-By: Claude ...` trailer in commit messages and no
  "Generated with Claude Code" line in PR descriptions.

## Running things

A local `.env` copied from `.env.example` is required at the repo root. Don't assume which Python
or Node the host has: the project needs Python 3.14 and Node 24. There are two ways to run it.

**Everything in Docker Compose**, from the repo root:

```bash
docker compose up --build -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_dev
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
```

**Only the database in Docker** (`docker compose up -d db`), with the backend in a Python 3.14
venv and the frontend on Node 24. Set the host in `DATABASE_URL` to `localhost` instead of `db`.
Settings don't read `.env` by themselves, so load it into the shell or the IDE's run
configuration first. See README "Running without Docker".

`seed_dev` runs only with `DEBUG` on. It creates the admin login `admin` / `admin` and fills the
next 7 days for every game with a seed hook.

URLs: frontend http://localhost:5173 (the game is at `/games/word`), API
http://localhost:8000/api/v1/, OpenAPI docs http://localhost:8000/api/docs/, admin
http://localhost:8000/admin/.

CI runs on every PR: `.github/workflows/backend.yml` (job `test`: ruff check, ruff format --check,
migrate, pytest against a Postgres service) and `.github/workflows/frontend.yml` (job `check`:
lint, type-check, test, build).

## Dependencies

**Backend:** managed with pip-tools. Edit `backend/requirements/base.in` (runtime) or `dev.in`
(dev/test), then recompile inside the container so pins resolve for Python 3.14:

```bash
docker compose run --rm backend pip-compile --strip-extras requirements/base.in
docker compose run --rm backend pip-compile --strip-extras requirements/dev.in
```

Never edit the `.txt` files by hand. Commit `.in` and `.txt` together.

**Frontend:** npm with exact pins (`.npmrc` has `save-exact=true`). Commit `package-lock.json`.

- TypeScript stays on 5.x: TypeScript 7 has no JS API, which `vue-tsc`, `typescript-eslint` and
  `openapi-typescript` need.
- `primeicons` stays on 7.0.0, the last MIT version; 8 is under the PrimeUI license.
- PrimeVue 5 requires a PrimeUI license key. None is configured yet, so every page shows an
  "Invalid PrimeUI License" badge; whether to get a key or downgrade is an open team decision.
  Don't hide the badge with code.

## Settings

`backend/config/settings/{base,dev,prod}.py`, selected via `DJANGO_SETTINGS_MODULE`. All
configuration comes from environment variables via django-environ (`DATABASE_URL`,
`DJANGO_SECRET_KEY`, ...). `TIME_ZONE = "Europe/Bucharest"`, `USE_TZ = True`.

`dev.py` trusts the Vite dev server in `CSRF_TRUSTED_ORIGINS`: cookies are shared across ports on
localhost, so an admin login reaches the game too, which makes Django check CSRF on its requests.

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
  `get_playable_puzzle(game, day)` (`NoPuzzleError` 404, `ArchiveUnavailableError` 403), the
  `<game_day:day>` URL converter (`today` or ISO date), `manage.py seed_dev`.
- `results`: `GameResult`, `start_or_resume`, `save_progress`, `complete` (`AlreadyPlayedError`
  409). `save_progress` and `complete` count active time, so games never compute a duration.
  `POST /api/v1/results/<game>/<game_day:day>/heartbeat/` is shared by all games
  (`NotStartedError` 404 before the game is opened).
- Frontend: see the Frontend section.
- Step-by-step for a new game: CONTRIBUTING "How to build a game".

### Dependency direction (enforced in review, not by tooling)

- `games/*` depend on `puzzles` and `results`, never on each other.
- `leaderboards` and `stats` only read from `results`.
- `common` imports from no other app.
- No circular imports.

### Word game (`apps/games/word`)

- `rules.py`: pure logic: `normalize` (lowercase, NFC, cedilla ş/ţ to ș/ț), the 31-letter alphabet
  (ă, â, î, ș, ț are separate letters), 5 letters and 6 attempts, Wordle coloring, and
  `score` (7 minus attempts when solved, 0 when failed).
- Models: `Word` (word bank, `is_answer`) and `WordPuzzle` (the day's answer).
- API: `GET /api/v1/games/word/<day>/` opens the game; `POST .../guess/` sends a guess. `answer`,
  `solved`, `score` and `duration_ms` are null until the game ends. `invalid` and `not_a_word`
  (400) don't use an attempt.
- `data/guesses.txt` (5-letter forms of LOC 5.0, dexonline) and `data/answers.txt` (hand-checked
  common words, all also valid guesses). `manage.py import_words` loads them and can run again
  safely; `seed_dev` loads them into an empty word bank.

## Code style

- ruff with line length 100, target py314; rules E, W, F, I, B, UP, DJ. Migrations are excluded.
- Backend tests use pytest + pytest-django; put them in each app's `tests/` package.

## Frontend

Run frontend tools with Node 24: on the host, or in the `frontend` compose service
(`docker compose exec frontend npm run lint`).

- Scripts: `dev`, `build`, `preview`, `test`, `lint`, `format`, `type-check`, `generate:api`.
- Feature-based layout in `frontend/src/`: `app/`, `api/` (only place that talks to the backend),
  `shared/`, `features/<name>/` (public entry `index.ts`), `locales/`, `tests/`.
- `eslint-plugin-boundaries` (v7 policy API) forbids cross-feature imports, deep imports into a
  feature from outside, and shared/api importing features. Components and views may not import
  `@/api` or PrimeVue. The boundaries rule is off in `*.test.ts`, so tests can use `src/tests`.
  Full rules in the root `CONTRIBUTING.md`.
- `src/api/generated/schema.d.ts` is generated by `npm run generate:api` and committed. Inside
  compose, pass `API_SCHEMA_URL=http://backend:8000/api/schema/`. The script uses POSIX shell
  syntax, so on Windows run it through Docker, WSL or Git Bash.
- All user-facing strings go through vue-i18n (`ro` is the default locale, `en` the second); add
  them to both `ro.json` and `en.json`.
- Feature tests go in the feature's `tests/`; `src/api`, `src/app` and `src/shared` keep them next
  to the file. `mountWithPlugins` in `src/tests/utils.ts` mounts with the app's plugins.

### Shared frontend pieces

- `src/api/http.ts`: `http` and `ApiError`.
- `src/shared/components`: `AppButton`, `AppCard`, `AppDialog`, `AppMessage`, `AppSpinner` wrap
  PrimeVue; use them instead of PrimeVue, and add a wrapper for any other component you need.
  Also `GameShell`, `ResultCard`, `ErrorState`. `ShareButton` and `Timer` are still placeholders.
- `src/shared/composables/useHeartbeat.ts`: beats every 15 s while active and the page is visible.
- `src/shared/stores/theme.ts`: light, dark or auto, remembered in the browser.
- `src/app/layouts/AppHeader.vue`: only the theme and RO/EN controls.

### Colors and icons

Colors come from the `--dz-*` variables in `src/app/styles/theme.css`; don't write colors in
components. `src/app/theme/preset.ts` makes PrimeVue components follow them. There are two greens
and two pinks, whose shades swap between light and dark mode:

- `--dz-primary`, `--dz-accent`: for design (buttons, highlights, decoration).
- `--dz-primary-strong`, `--dz-accent-strong`: stand out from the page. Green for confirmations
  and pink for errors, which are pink text with no background.

Dark mode is the `.app-dark` class on `<html>`. Icons are PrimeIcons classes (`pi pi-sun`).

## Docs and workflow

- There is a single `README.md` and a single `CONTRIBUTING.md`, both in the repo root, covering
  backend and frontend. Don't add per-folder READMEs.
- `main` is protected (ruleset `protect-main`): work on a branch and open a PR using the template.
  PRs need one approval from a teammate and passing `test` (Backend CI) and `check` (Frontend CI).
- PRs are squash-merged only (repository setting), so the PR title becomes the commit message.
  When a PR is stacked on another, rebase it onto `main` after the first one merges.
