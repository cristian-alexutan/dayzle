# Dayzle

A web platform with five daily puzzle games: a Romanian Wordle, a Queens-style logic game,
a "Make the Target" math game, a 5-question trivia quiz and a GeoGuesser for Cluj-Napoca.

- `backend/`: REST API (Python 3.14, Django 6.1, Django REST Framework, PostgreSQL)
- `frontend/`: Vue 3 client

## Backend setup

Requirements: Git and Docker (with Docker Compose).

```bash
# 1. Clone
git clone https://github.com/cristian-alexutan/dayzle.git
cd dayzle

# 2. Create your environment file
cp .env.example .env

# 3. Start PostgreSQL and the backend
docker compose up --build

# 4. In another terminal, apply migrations
docker compose exec backend python manage.py migrate
```

The API is then available at http://localhost:8000/api/v1/ and the OpenAPI docs at
http://localhost:8000/api/docs/.

### Running tests and linting

```bash
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
```

### Running without Docker

```bash
cd backend
python3.14 -m venv .venv  # requires Python 3.14 installed locally
source .venv/bin/activate
pip install -r requirements/dev.txt
```

You still need a PostgreSQL server: start only the database with `docker compose up db`, and
set `DATABASE_URL` in `.env` to use `localhost` instead of `db`. Then export the variables
(`set -a; source ../.env; set +a`) and run `python manage.py runserver` or `pytest`.

### Dependencies

Dependencies are managed with [pip-tools](https://github.com/jazzband/pip-tools) and pinned in
`backend/requirements/*.txt`. Do not edit the `.txt` files by hand:

1. Add or change the package in `requirements/base.in` (runtime) or `requirements/dev.in`
   (development and tests).
2. Recompile inside the container, so the pins are resolved for Python 3.14:
   ```bash
   docker compose run --rm backend pip-compile --strip-extras requirements/base.in
   docker compose run --rm backend pip-compile --strip-extras requirements/dev.in
   ```
3. Commit both the `.in` and `.txt` files.

### Settings

Settings live in `backend/config/settings/`, split into `base.py` (shared), `dev.py` and
`prod.py`. Choose one with `DJANGO_SETTINGS_MODULE`. All secrets and environment-specific values
come from environment variables; see `.env.example`.

## Backend architecture

The backend is a **modular monolith**: one Django project split into apps with clear
responsibilities.

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

### Dependency direction

Apps may only import from each other in these directions:

- `games/*` depend on `puzzles` and `results`, and **never** on each other.
- `leaderboards` and `stats` only **read** from `results`.
- `common` imports from **no** other app.
- No circular imports.

These rules are not enforced by tooling yet, so reviewers should check them in pull requests.
