# rescue-net.eu Responder App

Flutter responder app for rescue-net.eu. See
[`docs/project-manual.md`](../../docs/project-manual.md) — responsibilities
in §11.2, responder procedure in §20.3.

## Status

Working responder app (manual §20.3) against the live API:

- **Sign in** — dev login (production swaps in OIDC with verified accounts).
- **Alerts inbox** — pending support requests with Accept / Decline / More-info
  (manual §9.3); responded and timed-out alerts shown as history.
- **Missions** — list of missions the responder belongs to, and a **mission
  room**: join, **explicit consent dialog** before enabling live-location
  sharing (manual §16.2), share location, **real-time chat** over the mission
  WebSocket, task checklist (toggle status on tasks assigned to you), and leave.

### Architecture

- `lib/api_client.dart` — REST + WebSocket client (`missionEvents` stream).
- `lib/models.dart` — typed models mirroring `packages/shared/openapi.yaml`.
- `lib/session.dart` — `Session` (`ChangeNotifier`) holding auth + client.
- `lib/screens/` — login, home (alerts + missions tabs), mission room.
- Device GPS is stubbed to a representative sample; the platform geolocation
  plugin lands with the native build.

## Local development

Requires the [Flutter SDK](https://docs.flutter.dev/get-started/install)
(>= 3.4).

```bash
cd apps/mobile
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

End-to-end smoke test against a running API (PostGIS + Redis):

```bash
dart run tool/smoke.dart   # drives the responder client through the full flow
```

> Platform folders (`android/`, `ios/`) are generated locally with
> `flutter create .` and are intentionally not committed.
