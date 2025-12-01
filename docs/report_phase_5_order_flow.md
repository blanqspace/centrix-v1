# Centrix v1 – Phase 5 (Order-Modell, Execution, Risk-Integration) Bericht

## Überblick
Phase 5 erweitert Centrix v1 um einen paper-basierten Order-Flow mit Risiko-Integration und technischem IBKR-Client-Wrapper. Ziel ist ein Ende-zu-Ende-Pfad von Order-Anlage über Risiko-Prüfung bis zur (simulierten) Ausführung, ohne echte Strategien oder Slack-Anbindung.

## Technische Umsetzung
- Datenbank: `orders` (Status-Pipeline proposed → executing/failed/risk_blocked/executed) und `trades` (Platzhalter für Ausführungen) werden in `db.py:init_schema()` angelegt.
- Modelle: `order_model.py` definiert `NewOrder` (Eingangsdaten) und `OrderRecord` (persistierte Orders, inkl. Status/Error), mit `from_row` für DB-Zeilen.
- Service: `order_service.py`
  - `create_order_proposal` legt Orders mit Status `proposed` an.
  - `check_risk` wandelt Orders in `DummyOrder`, zieht Limits aus `risk.load_risk_limits`, prüft via `check_order_against_limits`, setzt bei Verstoß `risk_blocked` + `safe_mode`.
  - `execute_order` prüft Safe-Mode, ruft Risiko-Check, verbindet den IB-Client, setzt Status `executing`, ruft `ib_client.submit_market_order`, setzt Status `executed` oder `failed`, trennt immer.
- IB-Client: `ib_client.py` bietet `create_ib_client`/`connect_ib`/`disconnect_ib`/`is_ib_connected` und den Platzhalter `submit_market_order` (simuliert Erfolg bei bestehender Verbindung, liefert `(success, error)` zurück).
- CLI: `main.py` Befehl `run-order-demo` baut Demo-Order (AAPL buy 10), optionaler Gateway-Check, legt Order an, führt Risiko-Check aus, führt Order aus, zeigt finalen OrderRecord.

## DB- und Datenfluss
- `orders`: Persistiert Kernfelder (symbol, side, quantity, status, timestamps, optional error_message). Statuswechsel durch `order_service`.
- `trades`: vorbereitet für Ausführungen; enthält FK auf `orders` (noch keine Einträge in Phase 5).
- Heartbeats: Gateway-Status weiterhin über `heartbeats` (source="gateway"), aber Order-Status läuft isoliert in `orders`.

## Risk- und Safe-Mode-Integration
- Limits (`risk.max_order_size`, `risk.max_daily_loss` placeholder) werden aus `config_settings` geladen; `_parse_optional_float`/`get_config_float` sorgen für robuste Konvertierung.
- `check_risk` blockiert Orders über `risk_blocked`, setzt `safe_mode=True` und hinterlegt die Begründung in `error_message`.
- `execute_order` bricht ab, wenn Safe-Mode aktiv ist (Status `failed`, Fehler „Safe-Mode active").

## Execution-Pfad
- Verbindung: IB-Client mit Dummy-TCP-Connect (Platzhalter). Bei fehlender Verbindung Status `failed` mit Fehlertext.
- Order-Call: `submit_market_order` simuliert Market-Order; Erfolg → Status `executed`, Fehler → Status `failed` mit Text.
- Immer: sauberer Disconnect im `finally`-Block.

## Tests und erwartete Ergebnisse
- Demo: `python src/centrix/main.py run-order-demo` – legt Order an, prüft Risk, führt aus; Ausgabe zeigt Order-ID, Status und eventuelle Fehlermeldung.
- Risk-Block-Test: Setze `risk.max_order_size` klein (z. B. 1), führe `run-order-demo` → Status `risk_blocked`, Safe-Mode aktiv, Error-Begründung gesetzt.
- Safe-Mode-Test: Setze `safe_mode=true` vor dem Aufruf → `execute_order` setzt Status `failed` („Safe-Mode active"), keine Ausführung.
- Gateway-Fail-Test: Ungültigen Host/Port per Env setzen → Connect scheitert, Status `failed` („IB connection failed"), Heartbeat `gateway=disconnected` falls Connectivity-Check aktiv.

## Bewertung & Ausblick
- Phase 5 erfüllt den vorgesehenen Scope: Order-Modell + Status-Pipeline, Risiko-Integration mit Safe-Mode, minimaler IBKR-Execution-Stub und CLI-Demo. Keine Strategien/Slack implementiert, wie geplant.
- Nächste Schritte / Verbesserungen:
  1) Echte ib_insync/IBKR-API für Orders und Fills; `trades` füllen.
  2) Erweiterte Statuscodes/Events und Logging statt print.
  3) Retry-/Reconnect-Strategien und Heartbeat-Koppelung für Orders.
  4) max_daily_loss-Logik mit realer PnL-Berechnung und Persistenz.
  5) Testabdeckung (Unit-/Integration) für Order-Service und Risk-Flow.
