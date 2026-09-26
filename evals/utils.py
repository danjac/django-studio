"""Shared helpers: host ports for the Docker services, so runs never clash."""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def write_env(project: Path) -> None:
    """Write .env with free host ports so runs never clash with other stacks."""
    ports = free_ports()
    env = (project / ".env.example").read_text()
    env = env.replace("127.0.0.1:5432/", f"127.0.0.1:{ports['POSTGRES_PORT']}/")
    env = env.replace("127.0.0.1:6379/", f"127.0.0.1:{ports['REDIS_PORT']}/")
    env = env.replace("localhost:1025", f"localhost:{ports['MAILPIT_SMTP_PORT']}")
    env += "".join(f"{name}={port}\n" for name, port in ports.items())
    (project / ".env").write_text(env)


def free_ports() -> dict[str, str]:
    """Pick a free host port for each service Compose publishes."""
    return {
        name: str(free_port())
        for name in (
            "POSTGRES_PORT",
            "REDIS_PORT",
            "MAILPIT_WEB_PORT",
            "MAILPIT_SMTP_PORT",
        )
    }


def service_env(ports: dict[str, str]) -> dict[str, str]:
    """Environment variables pointing Compose and Django at the given ports."""
    return {
        **ports,
        "DATABASE_URL": (
            f"postgresql://postgres:password@127.0.0.1:{ports['POSTGRES_PORT']}/postgres"
        ),
        "REDIS_URL": f"redis://127.0.0.1:{ports['REDIS_PORT']}/0",
        "EMAIL_URL": f"smtp://localhost:{ports['MAILPIT_SMTP_PORT']}",
    }


def free_port() -> int:
    """Return a TCP port that is free right now."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
