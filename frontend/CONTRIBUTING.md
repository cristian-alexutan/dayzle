# Contributing to the Dayzle frontend

These rules keep the frontend consistent while many people work on it in parallel. Where a rule
can be checked by a tool, `npm run lint` enforces it and CI fails on violations. The rest are
checked in code review.

## Before opening a pull request

```bash
npm run lint
npm run type-check
npm test
npm run build
```

CI runs the same commands on every pull request that touches `frontend/`.

## Architecture rules

### 1. Components never call the backend directly

All HTTP traffic goes through `src/api/` (the HTTP wrapper and the generated client). Inside a
feature, `api/endpoints.ts` wraps the generated client and `api/queries.ts` exposes TanStack Query
hooks. Components and views use those hooks.

**Enforced by lint:** files in `features/*/components/` and `features/*/views/` may not import
`@/api`.

### 2. A feature never imports from another feature

If two features need the same thing, move it to `src/shared/`. `src/shared/` itself may not
import from features or from `src/api/`.

**Enforced by lint** (`boundaries/dependencies` in `eslint.config.js`).

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

## Conventions

- Vue components use `<script setup lang="ts">` and the Composition API.
- Component files are PascalCase (`WordBoard.vue`); composables start with `use` (`useTimer.ts`).
- Server state lives in TanStack Query. Pinia is only for small client state (current user,
  theme).
- Import from `src` with the `@/` alias.
- Tests go in the feature's `tests/` folder and are named `*.test.ts` or `*.spec.ts`.
- Formatting is Prettier's job: run `npm run format` and don't argue about style in review.

## Dependencies

Use npm. Versions are pinned exactly (`.npmrc` sets `save-exact=true`); commit
`package-lock.json` with every dependency change. Install inside the dev container
(`docker compose exec frontend npm install <pkg>`) or with Node 24 locally.
