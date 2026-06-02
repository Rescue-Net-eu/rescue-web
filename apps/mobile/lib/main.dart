import 'package:flutter/material.dart';

import 'session.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(RescueNetApp(session: Session()));
}

class RescueNetApp extends StatefulWidget {
  const RescueNetApp({super.key, required this.session});

  final Session session;

  @override
  State<RescueNetApp> createState() => _RescueNetAppState();
}

class _RescueNetAppState extends State<RescueNetApp> {
  @override
  void initState() {
    super.initState();
    widget.session.addListener(_onChange);
  }

  @override
  void dispose() {
    widget.session.removeListener(_onChange);
    super.dispose();
  }

  void _onChange() => setState(() {});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'rescue-net.eu',
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFFB00020),
        useMaterial3: true,
      ),
      home: widget.session.isAuthenticated
          ? HomeScreen(session: widget.session)
          : LoginScreen(session: widget.session),
    );
  }
}
