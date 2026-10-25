# Dayzle frontend

Vue 3 single-page app for Dayzle. It consumes the Django REST API under `/api/v1/`.

## Stack

- Vue 3 (Composition API, `<script setup>`), Vite, TypeScript
- Vue Router, Pinia (small client state only: current user, theme)
- TanStack Query for Vue (server state)
- PrimeVue as the UI library. **To be confirmed by the team**; Vuetify is the alternative.
- Leaflet (GeoGuesser map)
- vue-i18n (Romanian is the default locale)
- Vitest + Vue Test Utils, ESLint + Prettier
- Node.js 24 LTS and **npm**. Versions are pinned exactly in `package.json` (`.npmrc` sets
  `save-exact=true`), and `package-lock.json` is committed.

## Setup

### With Docker (recommended)

From the repository root, after copying `.env.example` to `.env` (see the root README):

```bash
docker compose up
```

This starts PostgreSQL, the backend and the Vite dev server. Open http://localhost:5173.
Requests to `/api` are proxied to the backend container.

Run frontend commands inside the container:

```bash
docker compose exec frontend npm run lint
docker compose exec frontend npm test
```

### Without Docker

Requires Node.js 24 or newer.

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev          # http://localhost:5173, proxies /api to http://localhost:8000
```

The backend must be running on port 8000 for API calls to work. To proxy elsewhere, set
`API_PROXY_TARGET` before starting the dev server.

### Scripts

| Script | What it does |
|---|---|
| `npm run dev` | Start the Vite dev server |
| `npm run build` | Production build into `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm test` | Run unit tests with Vitest (passes when there are no tests yet) |
| `npm run lint` | ESLint, including the architecture rules below |
| `npm run format` | Format `src/` with Prettier |
| `npm run type-check` | Type-check with `vue-tsc` |
| `npm run generate:api` | Generate TypeScript types from the backend's OpenAPI schema |

### Generating the API client

`npm run generate:api` reads the schema from `http://localhost:8000/api/schema/` and writes
`src/api/generated/schema.d.ts` with `openapi-typescript`. Inside docker compose, use the
backend's service name:

```bash
docker compose exec -e API_SCHEMA_URL=http://backend:8000/api/schema/ frontend npm run generate:api
```

The generated file is committed, so building the frontend never needs the backend to be running.
Regenerate it and commit the result whenever the backend API changes. The script uses POSIX
shell syntax, so on Windows run it through Docker, WSL or Git Bash.

### Production image

`Dockerfile` is a multi-stage build: Node builds the app, and nginx serves `dist/` with a fallback
to `index.html` for client-side routes.

```bash
docker build -t dayzle-frontend .
docker run -p 8080:80 dayzle-frontend
```

## Folder structure

```
src/
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

Every game feature has the same layout:

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

The other features use the same layout, with only the folders they need.

## Rules

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full list and how each one is enforced.

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
