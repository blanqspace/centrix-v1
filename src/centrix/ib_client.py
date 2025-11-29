from __future__ import annotations

import os
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class IBClient:
    host: str
    port: int
    client_id: int
    connected: bool = False
    _socket: Optional[socket.socket] = field(default=None, repr=False)


def _load_ibkr_settings() -> Dict[str, int | str]:
    """Load IBKR host/port/client_id from env or optional infra/ibkr.env file."""
    defaults = {"host": "127.0.0.1", "port": 4002, "client_id": 1}

    settings: Dict[str, int | str] = defaults.copy()

    env_host = os.getenv("IBKR_HOST")
    env_port = os.getenv("IBKR_PORT")
    env_client_id = os.getenv("IBKR_CLIENT_ID")

    infra_path = Path(__file__).resolve().parents[2] / "infra" / "ibkr.env"
    if infra_path.exists():
        for line in infra_path.read_text().splitlines():
            if not line or line.strip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().upper()
            value = value.strip()
            if key == "IBKR_HOST":
                settings["host"] = value
            elif key == "IBKR_PORT":
                try:
                    settings["port"] = int(value)
                except ValueError:
                    pass
            elif key == "IBKR_CLIENT_ID":
                try:
                    settings["client_id"] = int(value)
                except ValueError:
                    pass

    if env_host:
        settings["host"] = env_host
    if env_port:
        try:
            settings["port"] = int(env_port)
        except ValueError:
            pass
    if env_client_id:
        try:
            settings["client_id"] = int(env_client_id)
        except ValueError:
            pass

    return settings


def create_ib_client() -> IBClient:
    """Create an IBClient with connection parameters but no active connection."""
    settings = _load_ibkr_settings()
    return IBClient(
        host=str(settings["host"]), port=int(settings["port"]), client_id=int(settings["client_id"])
    )


def connect_ib(client: IBClient, timeout: float = 5.0) -> bool:
    """Attempt to connect to the IBKR gateway; return True on success."""
    try:
        sock = socket.create_connection((client.host, client.port), timeout=timeout)
        client._socket = sock
        client.connected = True
        return True
    except Exception as exc:
        print(f"[ib_client] connection failed: {exc}")
        client.connected = False
        client._socket = None
        return False


def disconnect_ib(client: IBClient) -> None:
    """Close the IBKR gateway connection if open."""
    try:
        if client._socket is not None:
            client._socket.close()
    finally:
        client._socket = None
        client.connected = False


def is_ib_connected(client: IBClient) -> bool:
    """Return the cached connection status of the IB client."""
    return client.connected
