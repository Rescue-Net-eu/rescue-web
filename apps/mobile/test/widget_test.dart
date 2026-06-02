import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rescue_net_mobile/main.dart';
import 'package:rescue_net_mobile/session.dart';

void main() {
  testWidgets('shows the login screen when unauthenticated',
      (WidgetTester tester) async {
    await tester.pumpWidget(RescueNetApp(session: Session()));

    expect(find.text('rescue-net.eu'), findsOneWidget);
    expect(find.text('Responder app'), findsOneWidget);
    expect(find.byType(FilledButton), findsWidgets);
    // The emergency-services disclaimer must be present (manual §3).
    expect(find.textContaining('112'), findsOneWidget);
  });

  testWidgets('email field is editable', (WidgetTester tester) async {
    await tester.pumpWidget(RescueNetApp(session: Session()));
    await tester.enterText(find.byType(TextField), 'me@example.org');
    expect(find.text('me@example.org'), findsOneWidget);
  });
}
