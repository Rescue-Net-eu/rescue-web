import 'package:flutter/material.dart';

import '../session.dart';
import '../widgets/disclaimer_banner.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.session});

  final Session session;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController(text: 'responder@example.org');
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.session.login(_email.text.trim());
    } catch (e) {
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text('rescue-net.eu',
                    style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: 4),
                const Text('Responder app',
                    style: TextStyle(color: Colors.black54)),
                const SizedBox(height: 24),
                TextField(
                  controller: _email,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(
                    labelText: 'Email',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                if (_error != null) ...[
                  Text(_error!, style: const TextStyle(color: Color(0xFFB00020))),
                  const SizedBox(height: 12),
                ],
                FilledButton(
                  onPressed: _busy ? null : _submit,
                  child: Text(_busy ? 'Signing in…' : 'Sign in'),
                ),
                const SizedBox(height: 24),
                const DisclaimerBanner(),
                const SizedBox(height: 12),
                const Text(
                  'Development sign-in. Production uses OIDC with verified '
                  'volunteer accounts.',
                  style: TextStyle(fontSize: 12, color: Colors.black54),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
