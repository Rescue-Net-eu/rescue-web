/// Runtime configuration for the responder app.
///
/// Override at build time with:
/// `flutter run --dart-define=API_BASE_URL=https://api.rescue-net.eu`
class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
}
