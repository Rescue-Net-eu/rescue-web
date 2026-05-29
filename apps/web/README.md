# rescue-net.eu Web Console

Next.js (App Router) dispatcher console for rescue-net.eu. See
[`docs/project-manual.md`](../../docs/project-manual.md) — responsibilities
in §11.2, environment variables in §18.7.

## Status

MVP **skeleton**: a landing page that reports backend API health. Incident
creation, mission monitoring and the live map follow (manual §27).

## Local development

```bash
cd apps/web
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL
npm run dev                  # http://localhost:3000
npm run lint
npm run typecheck
```
