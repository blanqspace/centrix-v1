# Centrix v1 – Phase 3 (Risk-Layer) Bericht

## Kurzüberblick
Phase 3 stellt einen technischen Risk-Layer bereit, der ohne IBKR-Anbindung und ohne echte Orders arbeitet. Er verwaltet Risk-Limits über die zentrale Config-DB, prüft Dummy-Orders gegen die hinterlegten Schwellen und aktiviert bei Verstoß den Safe-Mode. Die Phase ergänzt die bestehenden Core-Bausteine (DB, Config, Control, Engine-Loop) um ein wiederverwendbares Risk-Modul sowie CLI-Hooks für manuelle Demos.

## Technische Umsetzung
- `src/centrix/risk.py` definiert `RiskLimits` (max_daily_loss, max_order_size) und `DummyOrder` (symbol, side, quantity). `_parse_optional_float` wandelt Config-Werte robust in float oder None.
- `load_risk_limits()` zieht Limits aus `config_settings` (Schlüssel `risk.max_daily_loss`, `risk.max_order_size`) und liefert einen `RiskLimits`-Container.
- `check_order_against_limits()` prüft Dummy-Orders aktuell gegen `max_order_size`; bei Überschreitung kommt ein Ablehnungsgrund zurück (max_daily_loss als Platzhalter für spätere Logik).
- `evaluate_order()` lädt Limits, prüft die Order, gibt eine klare Konsolenausgabe aus und setzt bei Verstoß `safe_mode` via `control.set_safe_mode(True)`.
- Selftest im Modul initialisiert das Schema, setzt ein Beispiel-Limit und demonstriert erlaubte/blockierte Orders.
- `src/centrix/config_service.py` liefert mit `get_config_float` einen Komfort-Wrapper zum robusten Lesen von Float-Konfigurationen (Fallback auf Default/None). Andere Funktionen bleiben unverändert.
- `src/centrix/control.py` stellt Safe-Mode/Flags bereit, auf die der Risk-Layer zum Abschalten wechselt.

## CLI-Integration (main.py)
- Neue Befehle in `src/centrix/main.py`:
  - `run-risk-demo`: initiiert das Schema, setzt fehlende Limits (Defaults), zeigt Limits an, prüft eine kleine und eine große Dummy-Order; eine Limitüberschreitung aktiviert Safe-Mode und wird klar ausgegeben; Abschluss zeigt `safe_mode`-Status.
  - `show-safe-mode`: liest und zeigt den aktuellen Safe-Mode-Status.
- Bestehende Befehle bleiben erhalten (`init-db`, `run-engine`), wodurch Risk-Demos unabhängig vom Engine-Loop testbar sind.

## Daten- und Architektur-Perspektive
- Risk-Limits liegen als TEXT in `config_settings` (Keys `risk.max_daily_loss`, `risk.max_order_size`) und werden per `_parse_optional_float`/`get_config_float` zu Float/None konvertiert.
- Safe-Mode und weitere Flags liegen in `control_flags`; der Risk-Layer setzt `safe_mode` bei Verstößen.
- Im Architekturdiagramm (`diagrams/system_overview_v1.puml`) ist der Risk Service Teil von „Centrix Core“, mit Beziehungen `Engine Loop --> Risk Service` und `Risk Service --> Database`, was die Einbettung in Heartbeats/Control/Config/DB verdeutlicht.

## Test- und Demo-Szenarien
- Bereits demonstriert: `python src/centrix/main.py run-risk-demo` legt fehlende Limits an, zeigt Limits, erlaubt eine kleine Order, blockiert eine große Order und setzt anschließend Safe-Mode (`safe_mode=True`). `python src/centrix/main.py show-safe-mode` bestätigt den Status.
- Weitere sinnvolle Tests:
  - Grenzwerte: Order-Quantity exakt gleich `max_order_size` (soll erlaubt sein) und knapp darüber (soll blockieren).
  - Fehlende Config: Limits bewusst entfernen und prüfen, dass der Risk-Layer mit Defaults/None robust umgeht und keine Ausnahme wirft.
  - Regression mit Engine-Loop: Engine laufen lassen (`run-engine`), danach Risk-Demo ausführen und sicherstellen, dass State- und Safe-Mode-Flags sich nicht unerwartet beeinflussen.

## Bewertung und nächste Schritte
- Phase 3 erfüllt den vorgesehenen Scope für v1: Dummy-Risk-Prüfungen gegen `max_order_size`, Safe-Mode-Umschaltung, CLI-Demo und dokumentierte Einbettung in die Architektur. Kein IBKR- oder Echt-Order-Umfang enthalten, wie gefordert.
- Verbesserungs-/TODO-Ideen:
  1) max_daily_loss-Logik mit echter PnL-Berechnung ergänzen und persistieren.
  2) Logging statt `print` nutzen und ggf. Severity-Level einführen.
  3) Risk-Prüfung in den Engine-Loop integrieren (vor Auftragsausführung), inkl. Restart-/Safe-Mode-Flow.
  4) Testsuite für Risk (Unit-Tests mit Grenzwerten, fehlenden Configs, Safe-Mode-Pfaden).
  5) Optionale Konfiguration pro Scope/Nutzer für spätere Multi-User-Erweiterungen.
