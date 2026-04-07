from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from contract_review_langgraph.config import env_value, get_paths

VALID_CHECKPOINTERS = {"memory", "sqlite"}


def get_checkpointer_kind(kind: str | None = None) -> str:
    resolved = (kind or env_value("LANGGRAPH_CHECKPOINTER", "sqlite")).strip().lower()
    if resolved not in VALID_CHECKPOINTERS:
        raise ValueError(
            "LANGGRAPH_CHECKPOINTER must be one of: memory, sqlite. "
            f"Received: {resolved!r}"
        )
    return resolved


def create_checkpointer(
    kind: str | None = None,
    checkpoint_path: str | Path | None = None,
) -> Any:
    resolved_kind = get_checkpointer_kind(kind)
    if resolved_kind == "memory":
        return InMemorySaver()

    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
    except ImportError as exc:
        raise RuntimeError(
            "SQLite checkpointing requires the langgraph-checkpoint-sqlite package. "
            'Install dependencies from pyproject.toml or set LANGGRAPH_CHECKPOINTER="memory".'
        ) from exc

    db_path = Path(checkpoint_path) if checkpoint_path is not None else get_paths().checkpoint_db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # The FastAPI wrapper invokes the sync graph in worker threads, so the SQLite
    # connection has to be usable across threads for local demo traffic.
    connection = sqlite3.connect(db_path, check_same_thread=False)
    saver = SqliteSaver(connection)

    setup = getattr(saver, "setup", None)
    if callable(setup):
        setup()

    return saver
