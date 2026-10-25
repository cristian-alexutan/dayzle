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

## Dependencies

- **Backend:** edit `backend/requirements/*.in`, recompile with pip-tools inside the container,
  and commit the `.in` and `.txt` files together (see the README).
- **Frontend:** use npm. Versions are pinned exactly; commit `package-lock.json` with every
  dependency change.
