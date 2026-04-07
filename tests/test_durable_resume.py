from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from langgraph.types import Command

import api.main as api_main
from contract_review_langgraph import config as config_module
from contract_review_langgraph.audit import get_run, initialize_audit_store
from contract_review_langgraph.checkpointing import create_checkpointer, get_checkpointer_kind
from contract_review_langgraph.graph import build_graph


@pytest.fixture()
def isolated_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    source_root = Path(__file__).resolve().parents[1]
    policies_dir = tmp_path / "policies"
    policies_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        source_root / "policies" / "default_policy.yaml",
        policies_dir / "default_policy.yaml",
    )

    monkeypatch.setattr(config_module, "get_repo_root", lambda: tmp_path)
    monkeypatch.setenv("ALLOW_HEURISTIC_FALLBACK", "true")
    monkeypatch.setenv("LANGGRAPH_CHECKPOINTER", "sqlite")
    return tmp_path


def _interrupt_payload(compiled_graph, thread_id: str) -> dict:
    snapshot = compiled_graph.get_state({"configurable": {"thread_id": thread_id}})
    for task in snapshot.tasks:
        if task.interrupts:
            return task.interrupts[0].value
    raise AssertionError("Expected an interrupt payload for the test run.")


def test_checkpointer_defaults_to_sqlite_and_honors_memory_override(
    isolated_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sqlite_saver = create_checkpointer()
    assert get_checkpointer_kind() == "sqlite"
    assert type(sqlite_saver).__name__ == "SqliteSaver"
    assert (isolated_repo / "runtime" / "audit" / "checkpoints.sqlite3").exists()

    monkeypatch.setenv("LANGGRAPH_CHECKPOINTER", "memory")
    memory_saver = create_checkpointer()
    assert get_checkpointer_kind() == "memory"
    assert type(memory_saver).__name__ == "InMemorySaver"


def test_restart_simulation_preserves_interrupt_and_resume_state(isolated_repo: Path) -> None:
    graph_one = build_graph()
    thread_id = "restart-thread"
    contract_path = isolated_repo / "high-risk.txt"
    contract_path.write_text(
        "1. Liability\n\nVendor shall indemnify and hold harmless Customer with unlimited liability.",
        encoding="utf-8",
    )
    config = {"configurable": {"thread_id": thread_id}}

    graph_one.invoke(
        {
            "contract_path": str(contract_path),
            "provider": "openai",
            "thread_id": thread_id,
            "run_id": thread_id,
        },
        config,
    )

    payload = _interrupt_payload(graph_one, thread_id)
    assert payload["action_required"] == "review_contract"

    graph_two = build_graph()
    restarted_payload = _interrupt_payload(graph_two, thread_id)
    assert restarted_payload == payload

    graph_two.invoke(
        Command(
            resume={
                "decision": "approve",
                "reviewer_notes": "Approved after restart simulation.",
                "reviewer_id": "test-reviewer",
                "edited_extractions": [],
                "edited_risks": [],
            }
        ),
        config,
    )

    final_state = graph_two.get_state(config).values
    assert final_state["final_status"] == "approved_by_reviewer"
    assert final_state["review_status"] == "completed"


def test_api_status_and_pending_reviews_survive_resume(
    isolated_repo: Path,
) -> None:
    api_main.graph = build_graph()
    client = TestClient(api_main.app)

    run_response = client.post(
        "/api/run",
        data={
            "text": "1. Indemnity\n\nCustomer shall indemnify Vendor and hold it harmless with unlimited liability."
        },
    )
    assert run_response.status_code == 200
    interrupted = run_response.json()
    assert interrupted["status"] == "interrupted"
    thread_id = interrupted["thread_id"]

    status_response = client.get(f"/api/runs/{thread_id}")
    assert status_response.status_code == 200
    assert status_response.json() == interrupted

    pending_response = client.get("/api/pending-reviews")
    assert pending_response.status_code == 200
    pending_items = pending_response.json()["items"]
    assert len(pending_items) == 1
    assert pending_items[0]["thread_id"] == thread_id
    assert pending_items[0]["review_status"] == "pending"

    run_row = get_run(thread_id)
    assert run_row is not None
    assert run_row["review_status"] == "pending"
    assert run_row["interrupted_at"] is not None
    assert run_row["resumed_at"] is None

    resume_response = client.post(
        f"/api/resume/{thread_id}",
        json={
            "decision": "approve",
            "reviewer_notes": "Looks acceptable.",
            "reviewer_id": "api-reviewer",
            "edited_extractions": [],
            "edited_risks": [],
        },
    )
    assert resume_response.status_code == 200
    assert resume_response.json()["final_status"] == "approved_by_reviewer"

    completed_status = client.get(f"/api/runs/{thread_id}")
    assert completed_status.status_code == 200
    completed_body = completed_status.json()
    assert completed_body["status"] == "completed"
    assert completed_body["thread_id"] == thread_id
    assert completed_body["final_status"] == "approved_by_reviewer"

    pending_after_resume = client.get("/api/pending-reviews")
    assert pending_after_resume.status_code == 200
    assert pending_after_resume.json()["items"] == []

    run_row = get_run(thread_id)
    assert run_row is not None
    assert run_row["review_status"] == "completed"
    assert run_row["interrupted_at"] is not None
    assert run_row["resumed_at"] is not None


def test_low_risk_runs_do_not_enter_pending_reviews(isolated_repo: Path) -> None:
    api_main.graph = build_graph()
    client = TestClient(api_main.app)

    run_response = client.post(
        "/api/run",
        data={
            "text": "1. Fees\n\nCustomer pays invoices within 30 days of receipt."
        },
    )
    assert run_response.status_code == 200
    body = run_response.json()
    assert body["status"] == "completed"
    assert body["final_status"] == "approved_automatically"

    pending_response = client.get("/api/pending-reviews")
    assert pending_response.status_code == 200
    assert pending_response.json()["items"] == []


def test_schema_migration_adds_missing_columns(isolated_repo: Path) -> None:
    """_ensure_run_columns migrates an old-schema DB; verify every new column is added."""
    audit_dir = isolated_repo / "runtime" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    db_path = audit_dir / "audit.sqlite3"

    # Seed a DB with only the original pre-migration columns.
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE runs (
            run_id TEXT PRIMARY KEY,
            contract_id TEXT,
            contract_path TEXT,
            provider TEXT,
            policy_pack TEXT,
            final_status TEXT,
            route TEXT,
            report_path TEXT,
            started_at TEXT NOT NULL,
            completed_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    initialize_audit_store()

    conn = sqlite3.connect(str(db_path))
    present = {row[1] for row in conn.execute("PRAGMA table_info(runs)").fetchall()}
    conn.close()

    new_columns = {"thread_id", "file_name", "review_status", "interrupted_at", "resumed_at"}
    assert new_columns <= present, f"Missing columns after migration: {new_columns - present}"
