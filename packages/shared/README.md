# @rescue-net/shared

Shared API contract for rescue-net.eu (manual §12).

- `openapi.yaml` — the OpenAPI 3.1 contract. The FastAPI service is the
  source of truth at runtime (`/openapi.json`); this file is the
  human-maintained skeleton kept in sync as features land.

## Generating clients

Typed clients for the web console and mobile app can be generated from the
running API or from `openapi.yaml`, for example:

```bash
# TypeScript (web)
npx openapi-typescript packages/shared/openapi.yaml -o apps/web/lib/api-types.ts

# Dart (mobile)
dart run build_runner build   # with an openapi generator package configured
```
