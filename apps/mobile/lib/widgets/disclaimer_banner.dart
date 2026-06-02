import 'package:flutter/material.dart';

/// The mandatory positioning disclaimer (manual §3).
class DisclaimerBanner extends StatelessWidget {
  const DisclaimerBanner({super.key});

  @override
  Widget build(BuildContext context) {
    return const Card(
      color: Color(0xFFFFF8E1),
      child: Padding(
        padding: EdgeInsets.all(12),
        child: Text(
          'In life-threatening emergencies, contact your official emergency '
          'number (e.g. 112) first. rescue-net.eu coordinates volunteer support.',
          style: TextStyle(fontSize: 13),
        ),
      ),
    );
  }
}
