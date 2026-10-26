# Contributing to Dayzle

These rules keep the codebase consistent while many people work on it in parallel. Where a rule
can be checked by a tool, CI enforces it. The rest are checked in code review.

For setup, see the [README](README.md).

## Workflow

`main` is protected: nobody pushes to it directly, not even admins.

1. Create a branch from an up-to-date `main`:
   ```bash
   git switch main && git pull
   git switch -c <type>/<short-description>    # e.g. feat/word-keyboard, fix/streak-reset
   ```
2. Commit in small, focused steps, and push the branch.
3. Open a pull request (`gh pr create` or on GitHub) and fill in the template.
4. A pull request can be merged when:
   - **at least one teammate approved it** (you cannot approve your own PR, and new commits
     dismiss earlier approvals),
   - all review conversations are resolved,
   - both CI checks pass: `test` (Backend CI) and `check` (Frontend CI).
5. Pull requests are **squash-merged**: the whole PR becomes one commit on `main`, titled with
   the PR title. Write clear PR titles; your individual branch commits don't need polishing.

### Before opening a pull request

Run the same checks as CI:

```bash
# Backend
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
docker compose exec backend pytest

# Frontend
docker compose exec frontend npm run lint
docker compose exec frontend npm run type-check
docker compose exec frontend npm test
docker compose exec frontend npm run build
```

### Reviewing

When you review a pull request, check:

- the architecture rules below, especially the ones marked **checked in review**,
- that tests cover new behaviour,
- that no secrets or `.env` files are committed.

## Backend rules

### App layout

Each app under `backend/apps/` keeps the same files: `models.py`, `services.py` (write
operations and business rules), `selectors.py` (read queries), `api/{serializers,views,urls}.py`
and `tests/`. Each app's `api/urls.py` is mounted by `config/urls.py` under `/api/v1/`.

### Dependency direction

- `games/*` depend on `puzzles` and `results`, and never on each other.
- `leaderboards` and `stats` only read from `results`.
- `common` imports from no other app.
- No circular imports.

**Checked in review** (not enforced by tooling yet).

### Style

- ruff handles linting and formatting (line length 100). Run `ruff format .` and don't argue
  about style in review.
- Tests use pytest + pytest-django and live in each app's `tests/` package.

## Frontend rules

Rules 1–3 are enforced by `npm run lint` (configured in `frontend/eslint.config.js`).

### 1. Components never call the backend directly

All HTTP traffic goes through `src/api/` (the HTTP wrapper and the generated client). Inside a
feature, `api/endpoints.ts` wraps the generated client and `api/queries.ts` exposes TanStack Query
hooks. Components and views use those hooks.

**Enforced by lint:** files in `features/*/components/` and `features/*/views/` may not import
`@/api`.

### 2. A feature never imports from another feature

If two features need the same thing, move it to `src/shared/`. `src/shared/` itself may not
import from features or from `src/api/`.

**Enforced by lint** (`boundaries/dependencies`).

### 3. Code outside a feature imports only from that feature's `index.ts`

`index.ts` is the feature's public entry point: export from it what the rest of the app needs
(for example its routes). Deep imports such as `@/features/word/routes` from `src/app/` are
rejected.

**Enforced by lint** (`boundaries/dependencies`).

### 4. The backend is the source of truth

Instant UI feedback (highlighting a conflict, disabling a used tile) may live in the frontend.
Anything saved, scored, ranked or secret is computed or re-checked by the backend. The API never
sends data the player should not know yet (the Word answer, the correct trivia answer,
GeoGuesser coordinates before the guess), so never work around that in the client.

**Checked in review.**

### 5. Game rule checks stay inside their feature

Checks that give instant feedback for one game live in that game's `composables/`. Do not copy
backend validation logic into the frontend, and do not share one game's checks with another.

**Checked in review.**

### 6. Route guards are a UX convenience

Guards in `features/auth/guards.ts` (guest, user, subscriber, admin) only decide what to show
and where to redirect. The backend enforces access on every request, so never rely on a guard
for security.

**Checked in review.**

### 7. All user-facing strings go through vue-i18n

No hard-coded text in templates or scripts. Add keys to `src/locales/ro.json` (the default) and
`src/locales/en.json`.

**Checked in review.**

### Conventions

- Vue components use `<script setup lang="ts">` and the Composition API.
- Component files are PascalCase (`WordBoard.vue`); composables start with `use` (`useTimer.ts`).
- Server state lives in TanStack Query. Pinia is only for small client state (current user,
  theme).
- Import from `src` with the `@/` alias.
- Tests go in the feature's `tests/` folder and are named `*.test.ts` or `*.spec.ts`.
- Prettier handles formatting: run `npm run format` and don't argue about style in review.

## How to build a game

Each game lives in `backend/apps/games/<game>/` and `frontend/src/features/<game>/`, and builds
on the shared pieces described in the README (Shared building blocks for games). Replace
`word` / `WordPuzzle` below with your game.

### Backend

1. **Content model** in `models.py`, linked one-to-one to the calendar entry. Secret fields
   (answer, solution, coordinates) live here:
   ```python
   class WordPuzzle(TimeStampedModel):
       daily_puzzle = models.OneToOneField(DailyPuzzle, on_delete=models.CASCADE, related_name="word")
       answer = models.CharField(max_length=5)
   ```
2. **Register the game** in `apps.py`:
   ```python
   def ready(self):
       from apps.puzzles.registry import register_game
       from .models import WordPuzzle
       from .services import seed_puzzle

       register_game(key="word", name="Cuvântul zilei", content_model=WordPuzzle, seed=seed_puzzle)
   ```
   `seed(daily_puzzle)` creates sample content for `manage.py seed_dev`.
3. **Django admin** (`admin.py`): register the content model so admins can author puzzles. They
   first add a Daily puzzle (game + date), then its content.
4. **Services** (`services.py`) hold the game rules. Every action follows the same steps:
   ```python
   puzzle = get_playable_puzzle("word", day)       # access rules for the day
   result = start_or_resume(guest_id, puzzle)      # the player's GameResult
   ...check the guess against puzzle.word.answer...
   save_progress(result, {"guesses": guesses})     # while playing
   complete(result, solved=True, score=score)      # when the game ends
   ```
   Raise a `DomainError` subclass (in your app's `exceptions.py`) for game-specific errors.
5. **Scoring:** turn the raw result into `score`, where higher is always better (it's what
   leaderboards will sort on, then `duration_ms`). Document the formula in a docstring.
6. **API** (`api/`): thin views that take `guest_id = get_guest_id(request)`, validate input
   with a serializer, call one service and serialize the output. URLs use `<game_day:day>/`.
   **Serializers never include secret fields while the game is in progress**; reveal them only
   once the result is completed.
7. **Tests** in `tests/`: services (rules, scoring, play-once) and API (status codes, no secrets
   in responses). Use the `api_client` fixture and the factories in
   `apps/puzzles/tests/factories.py` and `apps/results/tests/factories.py`.

### Frontend

1. **Types:** after your backend endpoints are merged, run `npm run generate:api` (see the
   README) and commit `src/api/generated/schema.d.ts`.
2. **`api/endpoints.ts`:** thin functions using `http` from `@/api/http` and the generated
   types. **`api/queries.ts`:** TanStack Query hooks (`useQuery`, `useMutation`) used by your
   components.
3. **Errors** arrive as `ApiError`; handle the codes your game can get (`no_puzzle`,
   `already_played`, `invalid`, and your own).
4. **Views and components** in `views/` and `components/`; game-specific instant feedback in
   `composables/`. All strings in `src/locales/ro.json` and `en.json` under a `<game>.` prefix.
5. **Routes:** export them from `routes.ts` through your `index.ts` (path `/games/<game>`), and
   add them to `src/app/router/index.ts`.
6. **Tests** in `tests/`, mounting components with `mountWithPlugins` from `@/tests/utils`.

## Dependencies

- **Backend:** edit `backend/requirements/*.in`, recompile with pip-tools inside the container,
  and commit the `.in` and `.txt` files together (see the README).
- **Frontend:** use npm. Versions are pinned exactly; commit `package-lock.json` with every
  dependency change.
