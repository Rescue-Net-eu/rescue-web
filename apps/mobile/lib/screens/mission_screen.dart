import 'dart:async';

import 'package:flutter/material.dart';

import '../api_client.dart';
import '../models.dart';
import '../session.dart';

class MissionScreen extends StatefulWidget {
  const MissionScreen({
    super.key,
    required this.session,
    required this.missionId,
  });

  final Session session;
  final String missionId;

  @override
  State<MissionScreen> createState() => _MissionScreenState();
}

class _MissionScreenState extends State<MissionScreen> {
  ApiClient get _api => widget.session.api;
  String get _myId => widget.session.user!.id;

  Mission? _mission;
  List<ChatMessage> _messages = [];
  List<Task> _tasks = [];
  String? _error;
  StreamSubscription<MissionEvent>? _sub;

  final _draft = TextEditingController();
  final _scroll = ScrollController();

  @override
  void initState() {
    super.initState();
    _load();
    _connect();
  }

  @override
  void dispose() {
    _sub?.cancel();
    _draft.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final mission = await _api.getMission(widget.missionId);
      final messages = await _api.listMessages(widget.missionId);
      final tasks = await _api.listTasks(widget.missionId);
      if (!mounted) return;
      setState(() {
        _mission = mission;
        _messages = messages;
        _tasks = tasks;
      });
      _scrollToEnd();
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    }
  }

  void _connect() {
    _sub = _api.missionEvents(widget.missionId).listen(
      _onEvent,
      onError: (_) {/* socket dropped; REST state still valid */},
    );
  }

  void _onEvent(MissionEvent e) {
    switch (e.type) {
      case 'mission.chat_message':
        setState(() => _messages = [..._messages, ChatMessage.fromJson(e.data)]);
        _scrollToEnd();
        break;
      case 'mission.task_created':
      case 'mission.task_updated':
        _api.listTasks(widget.missionId).then((t) {
          if (mounted) setState(() => _tasks = t);
        }).catchError((_) {});
        break;
      case 'mission.status_changed':
      case 'mission.member_joined':
      case 'mission.member_left':
      case 'mission.closed':
        _load();
        break;
    }
  }

  void _scrollToEnd() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(_scroll.position.maxScrollExtent,
            duration: const Duration(milliseconds: 200), curve: Curves.easeOut);
      }
    });
  }

  MissionMember? get _me {
    final mission = _mission;
    if (mission == null) return null;
    for (final m in mission.members) {
      if (m.userId == _myId && m.leftAt == null) return m;
    }
    return null;
  }

  Future<void> _join({required bool liveLocation}) async {
    try {
      final mission =
          await _api.joinMission(widget.missionId, liveLocation: liveLocation);
      if (mounted) setState(() => _mission = mission);
    } catch (e) {
      _toast('$e');
    }
  }

  Future<void> _leave() async {
    try {
      final mission = await _api.leaveMission(widget.missionId);
      if (mounted) setState(() => _mission = mission);
    } catch (e) {
      _toast('$e');
    }
  }

  Future<void> _send() async {
    final text = _draft.text.trim();
    if (text.isEmpty) return;
    _draft.clear();
    try {
      await _api.postMessage(widget.missionId, text);
      // Echoed back over the socket; no optimistic insert.
    } catch (e) {
      _toast('$e');
    }
  }

  Future<void> _shareLocation() async {
    // The device GPS plugin lands with the platform integration; for now send
    // a representative sample so the consent + ingest path is exercised.
    try {
      await _api.postLocation(widget.missionId,
          latitude: 45.0, longitude: 25.0, accuracyM: 10);
      _toast('Location shared');
    } catch (e) {
      _toast('$e');
    }
  }

  Future<void> _toggleTask(Task task) async {
    final next = task.isDone ? 'open' : 'done';
    try {
      await _api.updateTaskStatus(widget.missionId, task.id, next);
      final tasks = await _api.listTasks(widget.missionId);
      if (mounted) setState(() => _tasks = tasks);
    } catch (e) {
      _toast('$e');
    }
  }

  void _toast(String msg) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final mission = _mission;
    return Scaffold(
      appBar: AppBar(
        title: Text('Mission ${widget.missionId.substring(0, 8)}'),
      ),
      body: mission == null
          ? Center(
              child: _error != null
                  ? Text(_error!, style: const TextStyle(color: Color(0xFFB00020)))
                  : const CircularProgressIndicator(),
            )
          : Column(
              children: [
                _statusBar(mission),
                Expanded(child: _chatList()),
                if (_tasks.isNotEmpty) _taskStrip(),
                if (!mission.isClosed) _composer(mission),
              ],
            ),
    );
  }

  Widget _statusBar(Mission mission) {
    final me = _me;
    final joined = me != null;
    return Material(
      color: const Color(0xFFF5F6F8),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          children: [
            Chip(label: Text(mission.status)),
            const Spacer(),
            if (mission.isClosed)
              const Text('Mission closed', style: TextStyle(color: Colors.black54))
            else if (!joined)
              FilledButton(
                onPressed: () => _join(liveLocation: false),
                child: const Text('Join'),
              )
            else ...[
              if (me.liveLocationEnabled)
                TextButton.icon(
                  onPressed: _shareLocation,
                  icon: const Icon(Icons.my_location, size: 18),
                  label: const Text('Share location'),
                )
              else
                TextButton(
                  onPressed: () => _confirmConsent(),
                  child: const Text('Enable location'),
                ),
              OutlinedButton(onPressed: _leave, child: const Text('Leave')),
            ],
          ],
        ),
      ),
    );
  }

  Future<void> _confirmConsent() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Share live location?'),
        content: const Text(
          'Your location will be visible to mission coordinators for the '
          'duration of this mission only. It stops automatically when you '
          'leave or the mission closes. You can disable it at any time.',
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('I consent')),
        ],
      ),
    );
    if (ok == true) {
      await _join(liveLocation: true);
    }
  }

  Widget _chatList() {
    if (_messages.isEmpty) {
      return const Center(
        child: Text('No messages yet.', style: TextStyle(color: Colors.black45)),
      );
    }
    return ListView.builder(
      controller: _scroll,
      padding: const EdgeInsets.all(12),
      itemCount: _messages.length,
      itemBuilder: (_, i) {
        final m = _messages[i];
        final mine = m.userId == _myId;
        return Align(
          alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 4),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            constraints: const BoxConstraints(maxWidth: 280),
            decoration: BoxDecoration(
              color: mine ? const Color(0xFFB00020) : const Color(0xFFECEFF1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              crossAxisAlignment:
                  mine ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                if (!mine)
                  Text(m.userId.substring(0, 8),
                      style: const TextStyle(
                          fontSize: 11, fontWeight: FontWeight.bold)),
                Text(m.message,
                    style: TextStyle(
                        color: mine ? Colors.white : Colors.black87)),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _taskStrip() {
    return Material(
      color: Colors.white,
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('TASKS',
                style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: Colors.black45)),
            ..._tasks.map((t) {
              final mine = t.assignedTo == _myId;
              return CheckboxListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                value: t.isDone,
                onChanged: mine ? (_) => _toggleTask(t) : null,
                title: Text(
                  t.title,
                  style: TextStyle(
                    decoration: t.isDone ? TextDecoration.lineThrough : null,
                    color: mine ? Colors.black87 : Colors.black45,
                  ),
                ),
                subtitle: mine ? null : const Text('assigned to another responder'),
              );
            }),
          ],
        ),
      ),
    );
  }

  Widget _composer(Mission mission) {
    final joined = _me != null;
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.all(8),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _draft,
                enabled: joined,
                decoration: InputDecoration(
                  hintText: joined ? 'Message…' : 'Join to chat',
                  border: const OutlineInputBorder(),
                  isDense: true,
                ),
                onSubmitted: (_) => _send(),
              ),
            ),
            IconButton(
              onPressed: joined ? _send : null,
              icon: const Icon(Icons.send),
              color: const Color(0xFFB00020),
            ),
          ],
        ),
      ),
    );
  }
}
