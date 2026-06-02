import 'package:flutter/material.dart';

import '../api_client.dart';
import '../models.dart';
import '../session.dart';
import 'mission_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.session});

  final Session session;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  ApiClient get _api => widget.session.api;

  List<Alert>? _alerts;
  List<Mission>? _missions;
  String? _error;

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    setState(() => _error = null);
    try {
      final alerts = await _api.listAlerts();
      final missions = await _api.listMissions();
      if (!mounted) return;
      setState(() {
        _alerts = alerts;
        _missions = missions;
      });
    } catch (e) {
      if (mounted) setState(() => _error = '$e');
    }
  }

  Future<void> _respond(Alert alert, String response) async {
    try {
      await _api.respondToAlert(alert.id, response);
      await _refresh();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('$e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('rescue-net.eu'),
          actions: [
            IconButton(
              onPressed: widget.session.logout,
              icon: const Icon(Icons.logout),
              tooltip: 'Sign out',
            ),
          ],
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Alerts'),
              Tab(text: 'Missions'),
            ],
          ),
        ),
        body: RefreshIndicator(
          onRefresh: _refresh,
          child: TabBarView(
            children: [
              _alertsTab(),
              _missionsTab(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _alertsTab() {
    if (_error != null) return _errorView();
    if (_alerts == null) {
      return const Center(child: CircularProgressIndicator());
    }
    final open = _alerts!.where((a) => a.isOpen).toList();
    final others = _alerts!.where((a) => !a.isOpen).toList();
    if (_alerts!.isEmpty) {
      return _emptyView('No alerts yet.');
    }
    return ListView(
      padding: const EdgeInsets.all(12),
      children: [
        if (open.isNotEmpty) ...[
          const _SectionHeader('Awaiting your response'),
          ...open.map(_openAlertCard),
        ],
        if (others.isNotEmpty) ...[
          const _SectionHeader('History'),
          ...others.map(_pastAlertTile),
        ],
      ],
    );
  }

  Widget _openAlertCard(Alert alert) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Support request',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text('Type: ${alert.alertType.replaceAll('_', ' ')}',
                style: const TextStyle(color: Colors.black54)),
            if (alert.expiryAt != null)
              Text('Expires ${_fmt(alert.expiryAt!)}',
                  style: const TextStyle(color: Colors.black54, fontSize: 12)),
            const SizedBox(height: 12),
            Row(
              children: [
                FilledButton(
                  onPressed: () => _respond(alert, 'yes'),
                  child: const Text('Accept'),
                ),
                const SizedBox(width: 8),
                OutlinedButton(
                  onPressed: () => _respond(alert, 'no'),
                  child: const Text('Decline'),
                ),
                const SizedBox(width: 8),
                TextButton(
                  onPressed: () => _respond(alert, 'need_details'),
                  child: const Text('More info'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _pastAlertTile(Alert alert) {
    final label = alert.status == 'timeout'
        ? 'Timed out'
        : 'Responded: ${alert.response ?? '—'}';
    return ListTile(
      dense: true,
      leading: Icon(
        alert.response == 'yes' ? Icons.check_circle : Icons.history,
        color: alert.response == 'yes' ? const Color(0xFF1B7F3B) : Colors.black38,
      ),
      title: Text(label),
      subtitle: Text(alert.alertType.replaceAll('_', ' ')),
    );
  }

  Widget _missionsTab() {
    if (_error != null) return _errorView();
    if (_missions == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_missions!.isEmpty) {
      return _emptyView('No missions yet. Accept an alert to be enrolled.');
    }
    return ListView(
      padding: const EdgeInsets.all(12),
      children: _missions!.map((m) {
        return Card(
          child: ListTile(
            title: Text('Mission ${m.id.substring(0, 8)}'),
            subtitle: Text('Status: ${m.status}'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.of(context).push(
              MaterialPageRoute(
                builder: (_) =>
                    MissionScreen(session: widget.session, missionId: m.id),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _errorView() => _emptyView(_error!, isError: true);

  Widget _emptyView(String message, {bool isError = false}) {
    return ListView(
      children: [
        Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            children: [
              Icon(isError ? Icons.error_outline : Icons.inbox,
                  size: 48, color: Colors.black26),
              const SizedBox(height: 12),
              Text(message,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                      color: isError ? const Color(0xFFB00020) : Colors.black54)),
              const SizedBox(height: 12),
              OutlinedButton(onPressed: _refresh, child: const Text('Retry')),
            ],
          ),
        ),
      ],
    );
  }

  static String _fmt(DateTime t) {
    final local = t.toLocal();
    return '${local.hour.toString().padLeft(2, '0')}:'
        '${local.minute.toString().padLeft(2, '0')}';
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(4, 12, 4, 6),
      child: Text(text.toUpperCase(),
          style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Colors.black45,
              letterSpacing: 0.5)),
    );
  }
}
