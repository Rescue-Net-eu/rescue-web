import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rescue_net_mobile/main.dart';

void main() {
  testWidgets('renders the responder home screen', (WidgetTester tester) async {
    await tester.pumpWidget(const RescueNetApp());

    expect(find.text('Responder app — MVP skeleton'), findsOneWidget);
    expect(find.byType(FilledButton), findsOneWidget);
  });
}
