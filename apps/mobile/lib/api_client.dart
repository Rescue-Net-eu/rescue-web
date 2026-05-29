import 'dart:convert';

import 'package:http/http.dart' as http;

import 'config.dart';

/// Thin client for the rescue-net.eu API.
///
/// Skeleton: only the health probe is wired up. Auth, alerts, mission
/// participation and location sharing follow the project manual (§27).
class ApiClient {
  ApiClient({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  final http.Client _client;
  final String _baseUrl;

  Future<bool> isHealthy() async {
    try {
      final resp = await _client
          .get(Uri.parse('$_baseUrl/healthz'))
          .timeout(const Duration(seconds: 5));
      if (resp.statusCode != 200) return false;
      final body = jsonDecode(resp.body) as Map<String, dynamic>;
      return body['status'] == 'ok';
    } catch (_) {
      return false;
    }
  }
}
