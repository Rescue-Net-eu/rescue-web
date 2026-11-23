/// Data models mirroring the rescue-net.eu API (packages/shared/openapi.yaml).
library;

class User {
  User({
    required this.id,
    required this.email,
    required this.role,
    this.fullName,
    required this.status,
  });

  final String id;
  final String email;
  final String? fullName;
  final String role;
  final String status;

  factory User.fromJson(Map<String, dynamic> j) => User(
        id: j['id'] as String,
        email: j['email'] as String,
        fullName: j['full_name'] as String?,
        role: j['role'] as String,
        status: j['status'] as String,
      );
}

class Alert {
  Alert({
    required this.id,
    required this.incidentId,
    required this.alertType,
    required this.status,
    this.response,
    this.expiryAt,
  });

  final String id;
  final String incidentId;
  final String alertType;
  final String status; // sent | responded | timeout
  final String? response;
  final DateTime? expiryAt;

  bool get isOpen => status == 'sent' && response == null;

  factory Alert.fromJson(Map<String, dynamic> j) => Alert(
        id: j['id'] as String,
        incidentId: j['incident_id'] as String,
        alertType: j['alert_type'] as String,
        status: j['status'] as String,
        response: j['response'] as String?,
        expiryAt: j['expiry_at'] != null
            ? DateTime.parse(j['expiry_at'] as String)
            : null,
      );
}

class MissionMember {
  MissionMember({
    required this.userId,
    required this.roleInMission,
    required this.liveLocationEnabled,
    this.leftAt,
  });

  final String userId;
  final String roleInMission;
  final bool liveLocationEnabled;
  final DateTime? leftAt;

  factory MissionMember.fromJson(Map<String, dynamic> j) => MissionMember(
        userId: j['user_id'] as String,
        roleInMission: j['role_in_mission'] as String,
        liveLocationEnabled: j['live_location_enabled'] as bool,
        leftAt: j['left_at'] != null
            ? DateTime.parse(j['left_at'] as String)
            : null,
      );
}

class Mission {
  Mission({
    required this.id,
    required this.incidentId,
    required this.status,
    required this.members,
    this.leadUserId,
  });

  final String id;
  final String incidentId;
  final String status;
  final String? leadUserId;
  final List<MissionMember> members;

  bool get isClosed => status == 'closed' || status == 'cancelled';

  factory Mission.fromJson(Map<String, dynamic> j) => Mission(
        id: j['id'] as String,
        incidentId: j['incident_id'] as String,
        status: j['status'] as String,
        leadUserId: j['lead_user_id'] as String?,
        members: (j['members'] as List<dynamic>)
            .map((m) => MissionMember.fromJson(m as Map<String, dynamic>))
            .toList(),
      );
}

class ChatMessage {
  ChatMessage({
    required this.id,
    required this.userId,
    required this.message,
    required this.createdAt,
  });

  final String id;
  final String userId;
  final String message;
  final DateTime createdAt;

  factory ChatMessage.fromJson(Map<String, dynamic> j) => ChatMessage(
        id: j['id'] as String,
        userId: j['user_id'] as String,
        message: j['message'] as String,
        createdAt: DateTime.parse(j['created_at'] as String),
      );
}

class Task {
  Task({
    required this.id,
    required this.title,
    required this.status,
    this.assignedTo,
  });

  final String id;
  final String title;
  final String status;
  final String? assignedTo;

  bool get isDone => status == 'done';

  factory Task.fromJson(Map<String, dynamic> j) => Task(
        id: j['id'] as String,
        title: j['title'] as String,
        status: j['status'] as String,
        assignedTo: j['assigned_to'] as String?,
      );
}

/// A realtime event from the mission WebSocket (manual §14.2).
class MissionEvent {
  MissionEvent({required this.type, required this.data});

  final String type;
  final Map<String, dynamic> data;

  factory MissionEvent.fromJson(Map<String, dynamic> j) => MissionEvent(
        type: j['type'] as String,
        data: (j['data'] as Map<String, dynamic>?) ?? const {},
      );
}
