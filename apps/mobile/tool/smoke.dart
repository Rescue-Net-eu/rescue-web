// Manual end-to-end smoke test of the responder ApiClient against a running
// API (PostGIS + Redis). Not part of the unit suite. Run with:
//   dart run tool/smoke.dart
//
// Seeds dispatcher/admin state with the raw http package, then drives the
// responder entirely through the app's ApiClient — login, alert inbox,
// accept, join with consent, live location, and chat over the WebSocket.
import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:rescue_net_mobile/api_client.dart';

const base = 'http://localhost:8000';

Future<String> _login(String email, String role) async {
  final r = await http.post(Uri.parse('$base/auth/dev/login'),
      headers: {'content-type': 'application/json'},
      body: jsonEncode({'email': email, 'role': role}));
  return jsonDecode(r.body)['access_token'] as String;
}

Future<Map<String, dynamic>> _post(
    String token, String path, Map<String, dynamic> body) async {
  final r = await http.post(Uri.parse('$base$path'),
      headers: {
        'content-type': 'application/json',
        'authorization': 'Bearer $token'
      },
      body: jsonEncode(body));
  return r.body.isEmpty
      ? <String, dynamic>{}
      : jsonDecode(r.body) as Map<String, dynamic>;
}

Future<void> main() async {
  final disp = await _login('smoke-disp@example.org', 'dispatcher');
  final admin = await _login('smoke-admin@example.org', 'platform_admin');

  // Drive the responder through the app's own client.
  final responder = ApiClient(baseUrl: base);
  await responder.devLogin('smoke-resp@example.org');
  final me = await responder.me();
  print('responder: ${me.id}');

  await _post(admin, '/responders', {
    'user_id': me.id,
    'latitude': 45.01,
    'longitude': 25.0,
    'verification_status': 'verified',
    'skills': ['first_aid'],
  });
  final incident = await _post(disp, '/incidents', {
    'title': 'Smoke',
    'priority': 'medium',
    'latitude': 45.0,
    'longitude': 25.0,
    'radius_m': 50000,
  });
  final incidentId = incident['id'] as String;
  await _post(disp, '/incidents/$incidentId/alerts', {});

  final alerts = await responder.listAlerts();
  final open = alerts.where((a) => a.isOpen).toList();
  print('open alerts: ${open.length}');
  await responder.respondToAlert(open.first.id, 'yes');

  final mission = await _post(disp, '/incidents/$incidentId/create-mission', {});
  final missionId = mission['id'] as String;
  final joined = await responder.joinMission(missionId, liveLocation: true);
  print('joined mission $missionId; members: ${joined.members.length}');

  final events = <String>[];
  final sub = responder.missionEvents(missionId).listen((e) => events.add(e.type));
  await Future<void>.delayed(const Duration(milliseconds: 600));
  await responder.postLocation(missionId,
      latitude: 45.01, longitude: 25.0, accuracyM: 8);
  await responder.postMessage(missionId, 'arrived on scene');
  await Future<void>.delayed(const Duration(seconds: 1));
  await sub.cancel();

  print('events: $events');
  final ok = events.contains('mission.chat_message') &&
      events.contains('mission.location_updated');
  print(ok ? 'SMOKE_OK' : 'SMOKE_FAIL');
  responder.close();
}
