import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

import 'config.dart';
import 'models.dart';

/// Raised for non-2xx API responses; carries the status and server detail.
class ApiException implements Exception {
  ApiException(this.statusCode, this.detail);
  final int statusCode;
  final String detail;
  @override
  String toString() => 'ApiException($statusCode): $detail';
}

/// Client for the rescue-net.eu API — the responder-facing subset
/// (auth, alerts, mission participation, chat, live location).
class ApiClient {
  ApiClient({http.Client? client, String? baseUrl})
      : _client = client ?? http.Client(),
        _baseUrl = baseUrl ?? AppConfig.apiBaseUrl;

  final http.Client _client;
  final String _baseUrl;

  /// Bearer token for authenticated requests; set after login.
  String? token;

  Map<String, String> _headers({bool json = false}) => {
        if (json) 'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

  Future<dynamic> _send(
    String method,
    String path, {
    Object? body,
  }) async {
    final uri = Uri.parse('$_baseUrl$path');
    final request = http.Request(method, uri)
      ..headers.addAll(_headers(json: body != null));
    if (body != null) request.body = jsonEncode(body);

    final streamed = await _client.send(request).timeout(
          const Duration(seconds: 15),
        );
    final resp = await http.Response.fromStream(streamed);

    if (resp.statusCode >= 200 && resp.statusCode < 300) {
      if (resp.body.isEmpty) return null;
      return jsonDecode(resp.body);
    }
    String detail = resp.reasonPhrase ?? 'Request failed';
    try {
      final decoded = jsonDecode(resp.body);
      if (decoded is Map && decoded['detail'] != null) {
        detail = decoded['detail'].toString();
      }
    } catch (_) {/* non-JSON body */}
    throw ApiException(resp.statusCode, detail);
  }

  Future<bool> isHealthy() async {
    try {
      final resp = await _client
          .get(Uri.parse('$_baseUrl/healthz'))
          .timeout(const Duration(seconds: 5));
      if (resp.statusCode != 200) return false;
      return (jsonDecode(resp.body) as Map<String, dynamic>)['status'] == 'ok';
    } catch (_) {
      return false;
    }
  }

  // --- Auth ---------------------------------------------------------------

  /// Developer login (non-production). Stores and returns the access token.
  Future<String> devLogin(String email, {String role = 'responder'}) async {
    final data = await _send('POST', '/auth/dev/login',
        body: {'email': email, 'role': role}) as Map<String, dynamic>;
    token = data['access_token'] as String;
    return token!;
  }

  Future<User> me() async =>
      User.fromJson(await _send('GET', '/me') as Map<String, dynamic>);

  // --- Alerts (responder inbox) -------------------------------------------

  Future<List<Alert>> listAlerts() async {
    final data = await _send('GET', '/alerts') as List<dynamic>;
    return data.map((e) => Alert.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Alert> respondToAlert(String alertId, String response) async {
    final data = await _send('POST', '/alerts/$alertId/respond',
        body: {'response': response}) as Map<String, dynamic>;
    return Alert.fromJson(data);
  }

  // --- Missions -----------------------------------------------------------

  Future<List<Mission>> listMissions() async {
    final data = await _send('GET', '/missions') as List<dynamic>;
    return data.map((e) => Mission.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Mission> getMission(String id) async =>
      Mission.fromJson(await _send('GET', '/missions/$id') as Map<String, dynamic>);

  /// Join a mission, optionally enabling live-location sharing (explicit
  /// consent — manual §16.2).
  Future<Mission> joinMission(String id, {bool liveLocation = false}) async {
    final data = await _send('POST', '/missions/$id/join',
        body: {'live_location_enabled': liveLocation}) as Map<String, dynamic>;
    return Mission.fromJson(data);
  }

  Future<Mission> leaveMission(String id) async =>
      Mission.fromJson(await _send('POST', '/missions/$id/leave')
          as Map<String, dynamic>);

  Future<List<ChatMessage>> listMessages(String id) async {
    final data = await _send('GET', '/missions/$id/messages') as List<dynamic>;
    return data
        .map((e) => ChatMessage.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ChatMessage> postMessage(String id, String message) async {
    final data = await _send('POST', '/missions/$id/messages',
        body: {'message': message}) as Map<String, dynamic>;
    return ChatMessage.fromJson(data);
  }

  Future<List<Task>> listTasks(String id) async {
    final data = await _send('GET', '/missions/$id/tasks') as List<dynamic>;
    return data.map((e) => Task.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Task> updateTaskStatus(
      String missionId, String taskId, String status) async {
    final data = await _send('PATCH', '/missions/$missionId/tasks/$taskId',
        body: {'status': status}) as Map<String, dynamic>;
    return Task.fromJson(data);
  }

  /// Post a live location sample (active member with consent — manual §16.2).
  Future<void> postLocation(
    String missionId, {
    required double latitude,
    required double longitude,
    double? accuracyM,
  }) async {
    await _send('POST', '/missions/$missionId/locations', body: {
      'latitude': latitude,
      'longitude': longitude,
      if (accuracyM != null) 'accuracy_m': accuracyM,
    });
  }

  // --- Realtime -----------------------------------------------------------

  /// Connect to a mission's realtime event stream. Yields decoded events.
  Stream<MissionEvent> missionEvents(String missionId) {
    final wsBase = _baseUrl.replaceFirst(RegExp(r'^http'), 'ws');
    final uri = Uri.parse(
        '$wsBase/ws/missions/$missionId?token=${Uri.encodeQueryComponent(token ?? '')}');
    final channel = WebSocketChannel.connect(uri);
    return channel.stream.map((raw) {
      final decoded = jsonDecode(raw as String) as Map<String, dynamic>;
      return MissionEvent.fromJson(decoded);
    });
  }

  void close() => _client.close();
}
