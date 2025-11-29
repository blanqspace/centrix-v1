# Centrix v1 – Implementierungsplan

## Phase 0 – Setup & Struktur
- Neues Repo `centrix-v1`
- Projektstruktur (src, docs, diagrams)
- `main.py` als einfacher Startpunkt
- Erstes Architektur-Diagramm (`system_overview_v1.puml`)

## Phase 1 – DB- & Config-Basis

## Phase 2 – Engine-Loop & Heartbeats
- Ziele:
  - Engine-Schleife ohne IBKR/Risk/Orders
  - Regelmäßige Heartbeats (`source="engine"`)
  - Engine-State in `control_flags` (starting/running/stopped)
  - Config-Version überwachen (Hot-Reload-Platzhalter)
- Dateien:
  - `src/centrix/heartbeat.py`
  - `src/centrix/engine_loop.py`
  - Erweiterungen in `src/centrix/control.py`
  - Erweiterungen in `src/centrix/main.py`
- Erwartete Ergebnisse:
  - `python src/centrix/main.py init-db` initialisiert das Schema
  - `python src/centrix/main.py run-engine` schreibt Heartbeats und beendet sich selbst (max_iterations)
  - Nach dem Lauf: `get_latest_heartbeat("engine")` liefert einen aktuellen Eintrag; `get_engine_state()` liefert `stopped`

## Phase 3 – Risk-Layer (max_daily_loss, max_order_size)

## Phase 4 – Slack & IBKR-Status

## Phase 5 – Paper-Trading (Strategien + Orders)
