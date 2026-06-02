import 'package:flutter_test/flutter_test.dart';
import 'package:rescue_net_mobile/models.dart';

void main() {
  test('Alert.fromJson and isOpen', () {
    final open = Alert.fromJson({
      'id': 'a1',
      'incident_id': 'i1',
      'alert_type': 'availability_request',
      'status': 'sent',
      'response': null,
      'expiry_at': '2026-01-01T12:00:00Z',
    });
    expect(open.isOpen, isTrue);
    expect(open.expiryAt, isNotNull);

    final answered = Alert.fromJson({
      'id': 'a2',
      'incident_id': 'i1',
      'alert_type': 'availability_request',
      'status': 'responded',
      'response': 'yes',
      'expiry_at': null,
    });
    expect(answered.isOpen, isFalse);
  });

  test('Mission.fromJson parses members and isClosed', () {
    final mission = Mission.fromJson({
      'id': 'm1',
      'incident_id': 'i1',
      'lead_user_id': 'u-lead',
      'status': 'active',
      'members': [
        {
          'user_id': 'u1',
          'role_in_mission': 'responder',
          'live_location_enabled': true,
          'left_at': null,
        },
      ],
    });
    expect(mission.isClosed, isFalse);
    expect(mission.members, hasLength(1));
    expect(mission.members.first.liveLocationEnabled, isTrue);

    final closed = Mission.fromJson({
      'id': 'm2',
      'incident_id': 'i1',
      'lead_user_id': null,
      'status': 'closed',
      'members': <dynamic>[],
    });
    expect(closed.isClosed, isTrue);
  });

  test('Task.isDone', () {
    final t = Task.fromJson({
      'id': 't1',
      'title': 'Survey',
      'status': 'done',
      'assigned_to': 'u1',
    });
    expect(t.isDone, isTrue);
  });

  test('MissionEvent.fromJson tolerates missing data', () {
    final e = MissionEvent.fromJson({'type': 'mission.closed'});
    expect(e.type, 'mission.closed');
    expect(e.data, isEmpty);
  });
}
