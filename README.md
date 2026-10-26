# Dayzle

A web platform with five daily puzzle games: a Romanian Wordle, a Queens-style logic game,
a "Make the Target" math game, a 5-question trivia quiz and a GeoGuesser for Cluj-Napoca.

- `backend/`: REST API under `/api/v1/` (Python 3.14, Django 6.1, Django REST Framework,
  drf-spectacular, PostgreSQL 16)
- `frontend/`: Vue 3 single-page app (Vite, TypeScript, Vue Router, Pinia, TanStack Query,
  PrimeVue, Leaflet, vue-i18n)

> **First demo (MVP): the five games only.** Everyone plays anonymously; login, subscriptions,
> archive, leaderboards, stats and friends come after the demo. See [MVP scope](#mvp-scope).

Before contributing, read [CONTRIBUTING.md](CONTRIBUTING.md). Building a game? Follow
[How to build a game](CONTRIBUTING.md#how-to-build-a-game).

## Quick start

Requirements: Git and Docker (with Docker Compose).

```bash
# 1. Clone
git clone https://github.com/cristian-alexutan/dayzle.git
cd dayzle

# 2. Create your environment files
cp .env.example .env
cp frontend/.env.example frontend/.env

# 3. Start PostgreSQL, the backend and the frontend dev server
docker compose up --build

# 4. In another terminal, apply migrations and create dev data
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_dev
```

`seed_dev` creates a Django admin login `admin` / `admin` (only works with `DEBUG` on) and
puzzles for the coming days for every game that provides a seed hook.

> **Set up before the backend foundation (PR #2) was merged?** The custom user model requires a
> one-time database reset: `docker compose down -v`, then steps 3 and 4 again.

| What | URL |
|---|---|
| Frontend (Vite dev server) | http://localhost:5173 |
| API | http://localhost:8000/api/v1/ |
| OpenAPI docs | http://localhost:8000/api/docs/ |

The frontend dev server proxies `/api` to the backend container.

## Tests and linting

Run the tools inside the containers, so everyone uses the same Python and Node versions.

```bash
# Backend
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .

# Frontend
docker compose exec frontend npm run lint
docker compose exec frontend npm run type-check
docker compose exec frontend npm test
docker compose exec frontend npm run build
```

CI (GitHub Actions) runs all of these on every pull request: `.github/workflows/backend.yml`
(ruff, migrate and pytest against a Postgres service) and `.github/workflows/frontend.yml`
(lint, type-check, test, build).

### Frontend scripts

| Script | What it does |
|---|---|
| `npm run dev` | Start the Vite dev server |
| `npm run build` | Production build into `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm test` | Run unit tests with Vitest (passes when there are no tests yet) |
| `npm run lint` | ESLint, including the architecture rules |
| `npm run format` | Format `src/` with Prettier |
| `npm run type-check` | Type-check with `vue-tsc` |
| `npm run generate:api` | Generate TypeScript types from the backend's OpenAPI schema |

## Running without Docker

You still need PostgreSQL: start only the database with `docker compose up db`, and set
`DATABASE_URL` in `.env` to use `localhost` instead of `db`.

**Backend** (requires Python 3.14):

```bash
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements/dev.txt
set -a; source ../.env; set +a
python manage.py runserver
```

**Frontend** (requires Node.js 24 or newer):

```bash
cd frontend
npm ci
npm run dev          # http://localhost:5173, proxies /api to http://localhost:8000
```

To proxy to a different backend address, set `API_PROXY_TARGET` before starting the dev server.

## Configuration

- **Root `.env`** (copied from `.env.example`): backend and database settings, read by
  docker compose and Django.
- **`frontend/.env`** (copied from `frontend/.env.example`): `VITE_API_BASE_URL` and
  `VITE_GOOGLE_CLIENT_ID`. Only variables prefixed with `VITE_` reach the browser.
- **Django settings** live in `backend/config/settings/`, split into `base.py` (shared), `dev.py`
  and `prod.py`. Choose one with `DJANGO_SETTINGS_MODULE`. Secrets and environment-specific
  values always come from environment variables.

## Dependencies

**Backend:** managed with [pip-tools](https://github.com/jazzband/pip-tools) and pinned in
`backend/requirements/*.txt`. Never edit the `.txt` files by hand:

1. Add or change the package in `requirements/base.in` (runtime) or `requirements/dev.in`
   (development and tests).
2. Recompile inside the container, so the pins are resolved for Python 3.14:
   ```bash
   docker compose run --rm backend pip-compile --strip-extras requirements/base.in
   docker compose run --rm backend pip-compile --strip-extras requirements/dev.in
   ```
3. Commit both the `.in` and `.txt` files.

**Frontend:** managed with **npm** on Node.js 24 LTS. Versions are pinned exactly (`.npmrc` sets
`save-exact=true`), and `package-lock.json` is committed. Install packages inside the container
(`docker compose exec frontend npm install <pkg>`).

## Generating the API client

`npm run generate:api` reads the backend's OpenAPI schema and writes
`frontend/src/api/generated/schema.d.ts` with `openapi-typescript`. With docker compose:

```bash
docker compose exec -e API_SCHEMA_URL=http://backend:8000/api/schema/ frontend npm run generate:api
```

Without an `API_SCHEMA_URL`, the script uses `http://localhost:8000/api/schema/`. The generated
file is committed, so building the frontend never needs the backend to be running. Regenerate
it and commit the result whenever the API changes. The script uses POSIX shell syntax, so on
Windows run it through Docker, WSL or Git Bash.

## Production frontend image

`frontend/Dockerfile` is a multi-stage build: Node builds the app, and nginx serves `dist/` with a
fallback to `index.html` for client-side routes.

```bash
docker build -t dayzle-frontend frontend
docker run -p 8080:80 dayzle-frontend
```

## MVP scope

The first demo only needs the five games playable. Decisions for the MVP:

- **Everyone is anonymous.** Each visitor gets a `guest_id` stored in their Django session.
  Play-once is per guest (clearing cookies resets it; it becomes strict once login exists).
  Admins log in to Django admin only.
- **Puzzles are hand-authored by admins in Django admin** (http://localhost:8000/admin/). A
  `DailyPuzzle` row is the calendar entry (game + date, no content); each game stores its
  content in its own model linked to that row. The admin warns about games with no puzzle in
  the next 7 days. A day without a puzzle shows "no puzzle today".
- **Only today's puzzle is playable.** URLs already take a date (`today` or `YYYY-MM-DD`), so
  the archive can be added later without changing them.
- **One `GameResult` per player and puzzle**, shared by all games: created when the player
  starts, holds progress in `details` (so a refresh restores the game), and is completed with
  `solved`, `score` (higher is better) and a server-measured `duration_ms`.
- **Validation:** Word and GeoGuesser check every guess on the server (the answer is secret);
  the logic and math games give instant feedback in the browser and are fully re-checked on
  submit.
- **UI library: PrimeVue** (Aura theme).

**After the demo** (already decided): Google login with session cookies, guest results moving
to the account on login, subscriptions set by admins, archive access for subscribers, per-game
daily and friends leaderboards (`score` descending, then `duration_ms`), stats and streaks.

## Architecture

### Backend: modular monolith

One Django project split into apps with clear responsibilities.

```
backend/
  config/                 settings/{base,dev,prod}.py, urls.py, wsgi.py, asgi.py
  apps/
    common/               shared utilities (time helpers, base classes, permissions, exception handling)
    accounts/             Google login, roles, profile
    social/               friends and friend requests
    puzzles/              daily puzzle storage by date, play-once rule, daily reset
    results/              result records shared by all games
    games/
      word/ logic/ math/ trivia/ geo/
    leaderboards/         daily and friends-only rankings
    stats/                streaks, per-game stats, badges
    subscriptions/        status, archive access, admin activate/cancel
```

Every app has the same layout:

```
<app>/
  apps.py
  models.py         database models
  services.py       write operations and business rules
  selectors.py      read queries
  api/
    serializers.py
    views.py
    urls.py         mounted by config/urls.py under /api/v1/<app>/
  tests/
```

### Shared building blocks for games

| Where | What |
|---|---|
| `common/time.py` | `today_in_romania()`: the only way to get the current game day (resets at midnight in Romania) |
| `common/players.py` | `get_guest_id(request)`: the player's id, created in the session on first use |
| `common/exceptions.py` | `DomainError`: base class for errors raised by services; the API turns them into the error format below |
| `puzzles/models.py` | `Game` choices and `DailyPuzzle(game, date)` |
| `puzzles/registry.py` | `register_game(key, name, content_model, seed=None)`, called from each game's `AppConfig.ready()` |
| `puzzles/selectors.py` | `get_playable_puzzle(game, day)`: today's puzzle, or `NoPuzzleError` (404) / `ArchiveUnavailableError` (403) |
| `results/services.py` | `start_or_resume`, `save_progress`, `complete` (raises `AlreadyPlayedError`, 409) |

### API conventions

- Game endpoints take the day in the URL with the `game_day` converter, which accepts `today`
  or `YYYY-MM-DD`:
  ```
  GET  /api/v1/games/<game>/<game_day:day>/            the puzzle (without secrets) and the player's state
  POST /api/v1/games/<game>/<game_day:day>/<action>/   e.g. guess/, submit/
  ```
- Every error has the same shape, whatever its cause:
  ```json
  {"error": {"code": "already_played", "message": "This puzzle has already been played.", "details": null}}
  ```
  Validation errors use the code `invalid` and put the field errors in `details`. The frontend
  receives them as an `ApiError` with `status`, `code`, `message` and `details`.

### Frontend: feature-based

```
frontend/src/
  app/                  main.ts, App.vue, router/, layouts/, styles/
  api/                  the only place that talks to the backend
    http.ts             HTTP wrapper
    generated/          output of npm run generate:api
  shared/
    components/         GameShell, ResultCard, ShareButton, Timer, ErrorState
    composables/        useTimer
    utils/
  features/
    auth/               Google login, guest identity, route guards
    word/ logic/ math/ trivia/ geo/
    leaderboards/
    stats/              profile, streaks, badges
    social/             friends
    archive/
    subscription/
    admin/
  locales/              ro.json (default), en.json
  tests/                shared test setup
```

Every game feature has the same layout. The other features use it too, with only the folders
they need.

```
features/<game>/
  index.ts              public entry: the only file other code may import from
  routes.ts
  types.ts
  api/
    endpoints.ts        thin wrappers over the generated client
    queries.ts          TanStack Query hooks
  components/
  composables/
  views/
  tests/
```

### Rules

The full rules, and how each one is enforced, are in [CONTRIBUTING.md](CONTRIBUTING.md). In
short:

**Backend dependency direction**

- `games/*` depend on `puzzles` and `results`, and **never** on each other.
- `leaderboards` and `stats` only **read** from `results`.
- `common` imports from **no** other app.
- No circular imports.

**Frontend**

1. Components never call the backend directly, only through `src/api/` and each feature's `api/`
   folder.
2. A feature never imports from another feature. Anything shared moves to `src/shared/`.
3. Code outside a feature imports only from that feature's `index.ts`.
4. Instant UI feedback may live in the frontend. Anything saved, scored, ranked or secret is
   computed or re-checked by the backend, and the client never receives data it should not know
   yet.
5. Game-specific rule checks stay inside their feature and are not copied from the backend.
6. Route guards (guest, user, subscriber, admin) are a UX convenience only; the backend enforces
   access.
7. All user-facing strings go through vue-i18n.
