# rescue-net.eu Web Console

Next.js (App Router) dispatcher console for rescue-net.eu. See
[`docs/project-manual.md`](../../docs/project-manual.md) — responsibilities
in §11.2, environment variables in §18.7.

## Status

Working dispatcher console (manual §11.2) against the live API:

- **Sign in** — dev login (email + role) → bearer token, persisted in
  `localStorage`; restored on reload via `/me`. Production swaps in OIDC
  (Authentik) + MFA behind the same `AuthProvider` seam.
- **Overview** — open-incident / active-mission counts and lists.
- **Incidents** — list, create (title/type/priority/location/radius), and a
  detail page with the full dispatch flow: **preview nearby responders**
  (geospatial candidates), **send alert** (with reason), **create mission**,
  close incident.
- **Missions** — list, plus a live **mission room**: status transitions,
  **chat**, **live responder map**, and **tasks** — all updating in real time
  over the mission WebSocket (Redis-backed), with auto-reconnect (§21).

### Architecture

- `app/lib/api.ts` — typed client mirroring `packages/shared/openapi.yaml`.
- `app/lib/auth.tsx` — `AuthProvider` / `useAuth` (token + user).
- `app/lib/useMissionSocket.ts` — `mission.*` event stream with backoff reconnect.
- `app/components/mini-map.tsx` — dependency-free SVG map (responder positions
  around the incident). A future increment can swap in Leaflet/MapLibre with
  real basemap tiles.

No runtime dependencies beyond Next/React — native `fetch` + `WebSocket`.

## Local development

```bash
cd apps/web
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                  # http://localhost:3000
npm run lint
npm run typecheck
npm run build
```

Run the API (`services/api`) with PostGIS + Redis so the console has a backend.
