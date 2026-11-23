import 'package:flutter/foundation.dart';

import 'api_client.dart';
import 'models.dart';

/// Holds the authenticated session and the shared API client. A
/// [ChangeNotifier] so the widget tree can rebuild on login/logout.
class Session extends ChangeNotifier {
  Session({ApiClient? api}) : api = api ?? ApiClient();

  final ApiClient api;
  User? _user;

  User? get user => _user;
  bool get isAuthenticated => _user != null;

  Future<void> login(String email, {String role = 'responder'}) async {
    await api.devLogin(email, role: role);
    _user = await api.me();
    notifyListeners();
  }

  void logout() {
    api.token = null;
    _user = null;
    notifyListeners();
  }
}
