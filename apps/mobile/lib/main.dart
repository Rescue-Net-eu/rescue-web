import 'package:flutter/material.dart';

import 'api_client.dart';

void main() {
  runApp(const RescueNetApp());
}

class RescueNetApp extends StatelessWidget {
  const RescueNetApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'rescue-net.eu',
      theme: ThemeData(colorSchemeSeed: Colors.red, useMaterial3: true),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiClient _api = ApiClient();
  String _status = 'Checking backend…';

  @override
  void initState() {
    super.initState();
    _checkHealth();
  }

  Future<void> _checkHealth() async {
    final healthy = await _api.isHealthy();
    if (!mounted) return;
    setState(() {
      _status = healthy ? 'Backend API: online' : 'Backend API: unreachable';
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('rescue-net.eu')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Responder app — MVP skeleton',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            const Card(
              color: Color(0xFFFFF8E1),
              child: Padding(
                padding: EdgeInsets.all(12),
                child: Text(
                  'In life-threatening emergencies, contact your official '
                  'emergency number (e.g. 112) first.',
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text(_status, style: const TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            FilledButton(
              onPressed: _checkHealth,
              child: const Text('Refresh status'),
            ),
          ],
        ),
      ),
    );
  }
}
