# rescue-net.eu Responder App

Flutter responder app for rescue-net.eu. See
[`docs/project-manual.md`](../../docs/project-manual.md) — responsibilities
in §11.2, responder procedure in §20.3.

## Status

MVP **skeleton**: a home screen that checks backend API health. Alert
display, availability response, mission participation and consent-based
location sharing (only during active missions, manual §16.2) follow.

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

> Platform folders (`android/`, `ios/`) are generated locally with
> `flutter create .` and are intentionally not committed in the skeleton.
