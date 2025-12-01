# Centrix v1 – Phase 4 (IBKR-Gateway-Client & Status) Bericht

## Kurzüberblick
Phase 4 liefert eine technische Anbindung an das IBKR-Gateway, beschränkt auf Verbindungsaufbau, Statusprüfung und sauberen Disconnect. Orders, Marktdaten oder Strategien sind explizit nicht Teil dieser Phase. Ziel ist ein stabiler „Kabeltest“, der den Gateway-Status erfassbar macht, ohne den Prozess bei Fehlern zu beenden.

## Technische Umsetzung
- `src/centrix/ib_client.py`: Stellt den `IBClient`-Typ bereit (host, port, client_id, Zustandsflag, internes Socket). `_load_ibkr_settings` liest Parameter aus Umgebungsvariablen (`IBKR_HOST/PORT/CLIENT_ID`) oder optional `infra/ibkr.env` mit Defaults (127.0.0.1:4002, client_id=1). API:
  - `create_ib_client()` erstellt einen parametrisierten, aber nicht verbundenen Client.
  - `connect_ib(client, timeout=5.0)` versucht eine TCP-Verbindung, liefert True/False und fängt Fehler ab (keine harten Abbrüche, Fehlerausgabe per print).
  - `disconnect_ib(client)` schließt die Verbindung sicher, mehrfach aufrufbar.
  - `is_ib_connected(client)` gibt den Verbindungsstatus zurück.
- `src/centrix/main.py` CLI-Befehle:
  - `test-ib-connection`: initiiert das Schema, baut einen Client, versucht Connect, schreibt einen Heartbeat (`source="gateway"`, Status „connected“ oder „disconnected“), gibt das Ergebnis aus, trennt immer sauber.
  - `show-gateway-status`: liest den letzten Gateway-Heartbeat und zeigt Status + Alter oder meldet „kein Heartbeat vorhanden“.
- `src/centrix/heartbeat.py` unterstützt generische Quellen; `write_heartbeat`/`get_latest_heartbeat` können mit `source="gateway"` genutzt werden, um Verbindungsstatus zu persistieren.

## Daten- und Architektur-Sicht
- Gateway-Status wird in der Tabelle `heartbeats` mit `source="gateway"` und einem Status-Text („connected“/„disconnected“) abgelegt. Zeitstempel basiert auf `int(time.time())` aus dem Heartbeat-Modul.
- Architektur (`diagrams/system_overview_v1.puml`): Im Centrix Core existiert ein IB Client, der zum externen „IBKR Gateway“ verbindet. Engine Loop kann den Client ansprechen; Heartbeats werden in der Database gespeichert. Risk/Engine/Config bleiben entkoppelt und werden nicht beeinflusst.

## Test- und Demo-Szenarien
- Typische manuelle Tests:
  - Gateway nicht erreichbar → `python src/centrix/main.py test-ib-connection` erzeugt Heartbeat `gateway/disconnected`, Konsole meldet „connection failed“; `show-gateway-status` zeigt den Fehlerzustand.
  - Gateway erreichbar → gleicher Befehl schreibt `gateway/connected`, Konsole meldet „connected“; `show-gateway-status` zeigt den frischen Status.
- Weitere sinnvolle Tests:
  1) Falscher Host/Port (absichtlich ungültig per Env/infra) → Verbindung muss fehlschlagen, keine Exceptions nach außen, Heartbeat = disconnected.
  2) Timeout-Verhalten prüfen (z. B. sehr kurzer Timeout) → erwartetes False, Heartbeat = disconnected.
  3) Wiederholungsversuch nach Fehlschlag → beim zweiten Aufruf mit korrekten Parametern soll der Status auf connected wechseln und Heartbeat aktualisiert werden.

## Bewertung & Ausblick
- Phase 4 deckt den geplanten Scope ab: technischer Connect/Status/Disconnect ohne Orders, robuste Fehlerbehandlung und Statuspersistenz via Heartbeats; CLI-Hooks ermöglichen manuelle Verbindungsprüfungen.
- Ideen für nächste Schritte:
  1) Umstieg auf `ib_insync` oder die offizielle TWS-API für echten Session-Handshake.
  2) Erweiterte Statuscodes (z. B. „connecting“, „auth_failed“, „timeout“) und strukturierte Logs statt print.
  3) Latenz- oder Roundtrip-Messung beim Connect-Test und Speicherung im Heartbeat.
  4) Automatische Reconnect-Strategie mit Backoff und Limitierung, plus Steuerung via `control_flags`.
  5) Integration in den Engine-Loop: periodische Gateway-Checks und Koppelung an safe_mode/restart_needed.
