import 'package:flutter/material.dart';

class AppTheme {

  static const Color skyBlue = Color(0xFF0284C7);
  static const Color trailEmerald = Color(0xFF10B981);
  static const Color deepNavy = Color(0xFF0F172A);
  static const Color dangerRed = Color(0xFFEF4444);

  static const Color surfaceLight = Color(0xFFF8FAFC);
  static const Color cardLight = Colors.white;
  static const Color textSecondary = Color(0xFF64748B);

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      scaffoldBackgroundColor: surfaceLight,
      colorScheme: const ColorScheme.light(
        primary: skyBlue,
        secondary: trailEmerald,
        surface: cardLight,
        error: dangerRed,
        onPrimary: Colors.white,
        onSecondary: Colors.white,
        onSurface: deepNavy,
        onError: Colors.white,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: deepNavy,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: skyBlue,
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, 52),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      cardTheme: CardThemeData(
        color: cardLight,
        elevation: 2,
        shadowColor: deepNavy.withValues(alpha: 0.08),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
      ),
    );
  }
}