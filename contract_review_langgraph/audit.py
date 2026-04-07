from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from contract_review_langgraph.config import ensure_runtime_dirs

logger = logging.getLogger(__name__)

RUN_COLUMNS: dict[str, str] = {
    "run_id": "TEXT PRIMARY KEY",
    "thread_id": "TEXT",
    "contract_id": "TEXT",
    "file_name": "TEXT",
    "contract_path": "TEXT",
    "provider": "TEXT",
    "policy_pack": "TEXT",
    "review_status": "TEXT",
    "final_status": "TEXT",
    "route": "TEXT",
    "report_path": "TEXT",
    "started_at": "TEXT NOT NULL",
    "interrupted_at": "TEXT",
    "resumed_at": "TEXT",
    "completed_at": "TEXT",
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def initialize_audit_store() -> Path:
    paths = ensure_runtime_dirs()
    conn = sqlite3.connect(paths.audit_db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                thread_id TEXT,
                contract_id TEXT,
                file_name TEXT,
                contract_path TEXT,
                provider TEXT,
                policy_pack TEXT,
                review_status TEXT,
                final_status TEXT,
                route TEXT,
                report_path TEXT,
                started_at TEXT NOT NULL,
                interrupted_at TEXT,
                resumed_at TEXT,
                completed_at TEXT
            )
            """
        )
        _ensure_run_columns(conn)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_runs_review_status ON runs(review_status, interrupted_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_runs_thread_id ON runs(thread_id)"
        )
        conn.commit()
    finally:
        conn.close()
    return paths.audit_db_path


def register_run(state: dict[str, Any]) -> None:
    paths = ensure_runtime_dirs()
    initialize_audit_store()
    conn = sqlite3.connect(paths.audit_db_path)
    try:
        conn.execute(
            """
            INSERT INTO runs (
                run_id,
                thread_id,
                contract_id,
                file_name,
                contract_path,
                provider,
                policy_pack,
                review_status,
                final_status,
                route,
                report_path,
                started_at,
                interrupted_at,
                resumed_at,
                completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                thread_id = COALESCE(excluded.thread_id, runs.thread_id),
                contract_id = COALESCE(excluded.contract_id, runs.contract_id),
                file_name = COALESCE(excluded.file_name, runs.file_name),
                contract_path = COALESCE(excluded.contract_path, runs.contract_path),
                provider = COALESCE(excluded.provider, runs.provider),
                policy_pack = COALESCE(excluded.policy_pack, runs.policy_pack),
                review_status = COALESCE(excluded.review_status, runs.review_status),
                final_status = COALESCE(excluded.final_status, runs.final_status),
                route = COALESCE(excluded.route, runs.route),
                report_path = COALESCE(excluded.report_path, runs.report_path)
            """,
            (
                state["run_id"],
                state.get("thread_id"),
                state.get("contract_id"),
                state.get("file_name"),
                state.get("contract_path"),
                state.get("provider"),
                state.get("policy_pack"),
                state.get("review_status", "not_required"),
                state.get("final_status"),
                state.get("route"),
                state.get("report_path"),
                _utc_now(),
                state.get("interrupted_at"),
                state.get("resumed_at"),
                None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def append_event(run_id: str, node_name: str, event_type: str, payload: dict[str, Any]) -> None:
    paths = ensure_runtime_dirs()
    initialize_audit_store()
    created_at = _utc_now()
    payload_json = json.dumps(payload, ensure_ascii=True, sort_keys=True)

    conn = sqlite3.connect(paths.audit_db_path)
    try:
        conn.execute(
            """
            INSERT INTO events (run_id, node_name, event_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, node_name, event_type, payload_json, created_at),
        )
        conn.commit()
    finally:
        conn.close()

    with paths.audit_log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "run_id": run_id,
                    "node_name": node_name,
                    "event_type": event_type,
                    "payload": payload,
                    "created_at": created_at,
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        handle.write("\n")


def finalize_run(state: dict[str, Any]) -> None:
    paths = ensure_runtime_dirs()
    initialize_audit_store()
    conn = sqlite3.connect(paths.audit_db_path)
    try:
        conn.execute(
            """
            UPDATE runs
            SET thread_id = ?,
                contract_id = ?,
                file_name = ?,
                provider = ?,
                policy_pack = ?,
                review_status = ?,
                final_status = ?,
                route = ?,
                report_path = ?,
                interrupted_at = COALESCE(?, interrupted_at),
                resumed_at = COALESCE(?, resumed_at),
                completed_at = ?
            WHERE run_id = ?
            """,
            (
                state.get("thread_id"),
                state.get("contract_id"),
                state.get("file_name"),
                state.get("provider"),
                state.get("policy_pack"),
                state.get("review_status", "not_required"),
                state.get("final_status"),
                state.get("route"),
                state.get("report_path"),
                state.get("interrupted_at"),
                state.get("resumed_at"),
                _utc_now(),
                state["run_id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_run(run_id_or_thread_id: str) -> dict[str, Any] | None:
    paths = ensure_runtime_dirs()
    initialize_audit_store()
    conn = sqlite3.connect(paths.audit_db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT *
            FROM runs
            WHERE run_id = ? OR thread_id = ?
            ORDER BY started_at DESC
            LIMIT 1
            """,
            (run_id_or_thread_id, run_id_or_thread_id),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return dict(row)


def list_pending_reviews() -> list[dict[str, Any]]:
    paths = ensure_runtime_dirs()
    initialize_audit_store()
    conn = sqlite3.connect(paths.audit_db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                run_id,
                thread_id,
                contract_id,
                file_name,
                contract_path,
                provider,
                policy_pack,
                route,
                review_status,
                started_at,
                interrupted_at
            FROM runs
            WHERE review_status = 'pending'
            ORDER BY interrupted_at DESC, started_at DESC
            """
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


def mark_review_pending(run_id: str) -> bool:
    return _transition_review_status(run_id, "pending", interrupted=True)


def mark_review_completed(run_id: str) -> bool:
    return _transition_review_status(run_id, "completed", resumed=True)


def write_report(state: dict[str, Any]) -> str:
    paths = ensure_runtime_dirs()
    report_path = paths.reports_dir / f"{state['run_id']}.md"
    extractions = state.get("extractions", [])
    policy_results = state.get("policy_results", {})
    review_decision = state.get("review_decision", {})

    lines = [
        f"# Contract Review Run {state['run_id']}",
        "",
        "## Summary",
        f"- Thread ID: `{state.get('thread_id', 'unknown')}`",
        f"- Contract ID: `{state.get('contract_id', 'unknown')}`",
        f"- Contract Path: `{state.get('contract_path', 'unknown')}`",
        f"- Provider: `{state.get('llm_metadata', {}).get('provider', state.get('provider', 'unknown'))}`",
        f"- Model: `{state.get('llm_metadata', {}).get('model', 'unknown')}`",
        f"- Route: `{state.get('route', 'unknown')}`",
        f"- Review Status: `{state.get('review_status', 'not_required')}`",
        f"- Final Status: `{state.get('final_status', 'unknown')}`",
        "",
        "## Policy Reasons",
    ]
    reasons = policy_results.get("reasons", [])
    if reasons:
        lines.extend([f"- {reason}" for reason in reasons])
    else:
        lines.append("- No policy escalation reasons.")

    lines.extend(
        [
            "",
            "## Clause Outcomes",
        ]
    )
    for extraction in extractions:
        lines.extend(
            [
                f"### {extraction['clause_id']} - {extraction['clause_type']}",
                f"- Risk: `{extraction['risk_level']}`",
                f"- Confidence: `{extraction['confidence']}`",
                f"- Summary: {extraction['summary']}",
            ]
        )
        if extraction.get("evidence_spans"):
            lines.append(f"- Evidence: {' | '.join(extraction['evidence_spans'][:2])}")
        lines.append("")

    if review_decision:
        lines.extend(
            [
                "## Reviewer Decision",
                f"- Decision: `{review_decision.get('decision', 'unknown')}`",
                f"- Notes: {review_decision.get('reviewer_notes', 'None')}",
                "",
            ]
        )

    report_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return str(report_path)


def _ensure_run_columns(conn: sqlite3.Connection) -> None:
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(runs)").fetchall()
    }
    for column_name, column_type in RUN_COLUMNS.items():
        if column_name in existing:
            continue
        conn.execute(f"ALTER TABLE runs ADD COLUMN {column_name} {column_type}")
        logger.warning(
            "Schema migration: added column '%s %s' to runs table.", column_name, column_type
        )


def _transition_review_status(
    run_id: str,
    review_status: str,
    *,
    interrupted: bool = False,
    resumed: bool = False,
) -> bool:
    paths = ensure_runtime_dirs()
    initialize_audit_store()
    conn = sqlite3.connect(paths.audit_db_path)
    try:
        row = conn.execute(
            "SELECT review_status, interrupted_at, resumed_at FROM runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return False
        current_status, current_interrupted_at, current_resumed_at = row
        if current_status == review_status:
            return False

        interrupted_at = current_interrupted_at
        resumed_at = current_resumed_at
        now = _utc_now()
        if interrupted and not interrupted_at:
            interrupted_at = now
        if resumed and not resumed_at:
            resumed_at = now

        conn.execute(
            """
            UPDATE runs
            SET review_status = ?,
                interrupted_at = ?,
                resumed_at = ?
            WHERE run_id = ?
            """,
            (review_status, interrupted_at, resumed_at, run_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()
