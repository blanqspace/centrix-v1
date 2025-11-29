# Centrix v1 – Architekturübersicht

Centrix v1 richtet sich auf einen Single-User-Einsatz und läuft als Paper-Trading-Setup (IBKR-Paper), ausgelegt auf Stabilität und gute Debugbarkeit. Die Engine bleibt klein, kontrollierbar und testbar, bevor weitere Nutzer- oder Live-Funktionen hinzukommen.

Die Architektur trennt Infrastruktur und Steuerung klar: ein schlanker Kern übernimmt Engine, Risk-Checks, Monitoring und Konfiguration; Anbindungen bleiben austauschbar, damit spätere Containerisierung oder Skalierung möglich ist.

Kernkomponenten:
- IBKR-Gateway (später eigener Container)
- Centrix Core (Engine + Risk + Monitor + Config-Service)
- Datenbank (zuerst SQLite, später PostgreSQL)
- Slack (Control, Notify) als UI, ohne Business-Logik.
