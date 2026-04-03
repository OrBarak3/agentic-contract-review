from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from contract_review_langgraph.config import ensure_runtime_dirs


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
            INSERT OR REPLACE INTO runs (
                run_id,
                contract_id,
                contract_path,
                provider,
                policy_pack,
                final_status,
                route,
                report_path,
                started_at,
                completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state["run_id"],
                state.get("contract_id"),
                state.get("contract_path"),
                state.get("provider"),
                state.get("policy_pack"),
                state.get("final_status"),
                state.get("route"),
                state.get("report_path"),
                _utc_now(),
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
            SET contract_id = ?,
                provider = ?,
                policy_pack = ?,
                final_status = ?,
                route = ?,
                report_path = ?,
                completed_at = ?
            WHERE run_id = ?
            """,
            (
                state.get("contract_id"),
                state.get("provider"),
                state.get("policy_pack"),
                state.get("final_status"),
                state.get("route"),
                state.get("report_path"),
                _utc_now(),
                state["run_id"],
            ),
        )
        conn.commit()
    finally:
        conn.close()


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
        f"- Contract ID: `{state.get('contract_id', 'unknown')}`",
        f"- Contract Path: `{state.get('contract_path', 'unknown')}`",
        f"- Provider: `{state.get('llm_metadata', {}).get('provider', state.get('provider', 'unknown'))}`",
        f"- Model: `{state.get('llm_metadata', {}).get('model', 'unknown')}`",
        f"- Route: `{state.get('route', 'unknown')}`",
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

