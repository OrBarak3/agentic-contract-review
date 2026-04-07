from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from langgraph.types import interrupt

from contract_review_langgraph.audit import (
    append_event,
    finalize_run,
    mark_review_completed,
    mark_review_pending,
    register_run,
    write_report,
)
from contract_review_langgraph.config import get_paths
from contract_review_langgraph.llm import extract_contract_details
from contract_review_langgraph.parsing import UnsupportedDocumentError, chunk_into_clauses, compute_file_hash, normalize_text, read_contract
from contract_review_langgraph.policies import evaluate_policy, load_policy_pack


def ingest_contract(state: dict[str, Any]) -> dict[str, Any]:
    contract_path = Path(state["contract_path"]).expanduser()
    thread_id = state.get("thread_id") or state.get("run_id")
    run_id = state.get("run_id") or thread_id or str(uuid.uuid4())
    if not contract_path.exists() or not contract_path.is_file():
        failed_state = {
            "run_id": run_id,
            "thread_id": thread_id or run_id,
            "route": "audit_only",
            "review_status": "not_required",
            "final_status": "failed",
            "error": f"contract_path_not_found:{contract_path}",
            "contract_path": str(contract_path),
        }
        register_run(failed_state)
        append_event(run_id, "ingest_contract", "ingest_failed", {"error": failed_state["error"]})
        return failed_state

    contract_hash = compute_file_hash(contract_path)
    contract_id = contract_hash[:12]
    next_state = {
        "run_id": run_id,
        "thread_id": thread_id or run_id,
        "contract_id": contract_id,
        "contract_hash": contract_hash,
        "file_name": contract_path.name,
        "contract_path": str(contract_path),
        "provider": state.get("provider", "openai"),
        "policy_pack": state.get("policy_pack") or str(get_paths().default_policy_path),
        "parse_status": "pending",
        "review_status": "not_required",
    }
    register_run(next_state)
    append_event(
        run_id,
        "ingest_contract",
        "ingested",
        {
            "contract_id": contract_id,
            "contract_path": str(contract_path),
            "provider": next_state["provider"],
            "policy_pack": next_state["policy_pack"],
        },
    )
    return next_state


def parse_and_chunk_clauses(state: dict[str, Any]) -> dict[str, Any]:
    if state.get("final_status") == "failed":
        return {}

    contract_path = Path(state["contract_path"])
    try:
        raw_text, file_type = read_contract(contract_path)
        normalized_text = normalize_text(raw_text)
        clauses = [clause.model_dump() for clause in chunk_into_clauses(normalized_text)]
        if not clauses:
            raise UnsupportedDocumentError("document_contains_no_parsable_clauses")
        result = {
            "raw_text": normalized_text,
            "file_type": file_type,
            "clauses": clauses,
            "parse_status": "parsed",
        }
        append_event(
            state["run_id"],
            "parse_and_chunk_clauses",
            "parsed",
            {"file_type": file_type, "clause_count": len(clauses)},
        )
        return result
    except UnsupportedDocumentError as exc:
        result = {
            "parse_status": "needs_manual_parse",
            "parse_error": str(exc),
            "route": "audit_only",
            "final_status": "needs_manual_parse",
        }
        append_event(
            state["run_id"],
            "parse_and_chunk_clauses",
            "parse_unsupported",
            {"error": str(exc)},
        )
        return result


def extract_details_and_flag_risk(state: dict[str, Any]) -> dict[str, Any]:
    clauses = state.get("clauses", [])
    if not clauses:
        append_event(
            state["run_id"],
            "extract_details_and_flag_risk",
            "extraction_failed",
            {"error": "no_clauses_available_for_extraction"},
        )
        return {
            "route": "audit_only",
            "final_status": "failed",
            "error": "no_clauses_available_for_extraction",
        }

    try:
        extractions, metadata = extract_contract_details(clauses, state.get("provider", "openai"))
        append_event(
            state["run_id"],
            "extract_details_and_flag_risk",
            "extracted",
            {
                "provider": metadata.get("provider"),
                "model": metadata.get("model"),
                "fallback_used": metadata.get("fallback_used", False),
                "clause_count": len(extractions),
            },
        )
        return {"extractions": extractions, "llm_metadata": metadata}
    except Exception as exc:
        append_event(
            state["run_id"],
            "extract_details_and_flag_risk",
            "extraction_failed",
            {"error": str(exc)},
        )
        return {
            "route": "audit_only",
            "final_status": "failed",
            "error": f"extraction_failed:{exc}",
        }


def check_policy_rules(state: dict[str, Any]) -> dict[str, Any]:
    policy_path = Path(state.get("policy_pack") or get_paths().default_policy_path)
    try:
        policy_pack = load_policy_pack(policy_path)
        evaluation = evaluate_policy(state.get("extractions", []), policy_pack)
        append_event(
            state["run_id"],
            "check_policy_rules",
            "policy_evaluated",
            {
                "route": evaluation.route,
                "reasons": evaluation.reasons,
                "policy_pack": policy_pack.get("name", policy_path.name),
                "policy_version": policy_pack.get("version", "v1"),
            },
        )
        return {
            "route": evaluation.route,
            "policy_results": evaluation.model_dump(),
            "policy_pack_name": policy_pack.get("name", policy_path.name),
            "policy_pack_version": policy_pack.get("version", "v1"),
        }
    except Exception as exc:
        append_event(
            state["run_id"],
            "check_policy_rules",
            "policy_failed",
            {"error": str(exc), "policy_pack": str(policy_path)},
        )
        return {
            "route": "audit_only",
            "final_status": "failed",
            "error": f"policy_failed:{exc}",
        }


def auto_advance_standard_cases(state: dict[str, Any]) -> dict[str, Any]:
    result = {
        "final_status": "approved_automatically",
        "review_status": "not_required",
        "review_decision": {
            "decision": "auto_approve",
            "reviewer_notes": "Policy auto-pass conditions satisfied.",
        },
    }
    append_event(
        state["run_id"],
        "auto_advance_standard_cases",
        "auto_approved",
        {"reason": "policy_auto_pass"},
    )
    return result


def human_review(state: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "action_required": "review_contract",
        "thread_id": state.get("thread_id", state.get("run_id")),
        "contract_id": state.get("contract_id"),
        "route": state.get("route"),
        "policy_reasons": state.get("policy_results", {}).get("reasons", []),
        "extractions": state.get("extractions", []),
        "instructions": {
            "allowed_decisions": ["approve", "edit", "reject"],
            "resume_with": {
                "decision": "approve | edit | reject",
                "edited_extractions": [],
                "edited_risks": [],
                "reviewer_notes": "string",
                "reviewer_id": "string",
            },
        },
    }
    if mark_review_pending(state["run_id"]):
        append_event(
            state["run_id"],
            "human_review",
            "human_review_pending",
            {
                "thread_id": state.get("thread_id"),
                "policy_reasons": state.get("policy_results", {}).get("reasons", []),
            },
        )
    response = interrupt(payload)
    if mark_review_completed(state["run_id"]):
        append_event(
            state["run_id"],
            "human_review",
            "human_review_resumed",
            {
                "thread_id": state.get("thread_id"),
            },
        )
    normalized = _normalize_review_response(response)
    updated_extractions = _apply_reviewer_edits(
        state.get("extractions", []),
        normalized.get("edited_extractions", []),
        normalized.get("edited_risks", []),
    )

    decision = normalized["decision"]
    if decision == "reject":
        final_status = "rejected_by_reviewer"
    elif decision == "edit":
        final_status = "approved_with_edits"
    else:
        final_status = "approved_by_reviewer"

    append_event(
        state["run_id"],
        "human_review",
        "human_review_completed",
        {
            "decision": decision,
            "reviewer_id": normalized.get("reviewer_id"),
            "reviewer_notes": normalized.get("reviewer_notes"),
        },
    )
    return {
        "review_decision": normalized,
        "extractions": updated_extractions,
        "review_status": "completed",
        "final_status": final_status,
    }


def audit_and_report(state: dict[str, Any]) -> dict[str, Any]:
    report_path = write_report(state)
    append_event(
        state["run_id"],
        "audit_and_report",
        "report_written",
        {
            "final_status": state.get("final_status"),
            "route": state.get("route"),
            "report_path": report_path,
        },
    )
    completed_state = {"report_path": report_path}
    merged = dict(state)
    merged.update(completed_state)
    finalize_run(merged)
    return completed_state


def _normalize_review_response(response: Any) -> dict[str, Any]:
    if isinstance(response, str):
        return {
            "decision": response,
            "edited_extractions": [],
            "edited_risks": [],
            "reviewer_notes": "",
            "reviewer_id": "",
        }
    if not isinstance(response, dict):
        raise ValueError(f"Unexpected review response: {response!r}")
    normalized = {
        "decision": response.get("decision", "approve"),
        "edited_extractions": response.get("edited_extractions", []),
        "edited_risks": response.get("edited_risks", []),
        "reviewer_notes": response.get("reviewer_notes", ""),
        "reviewer_id": response.get("reviewer_id", ""),
    }
    if normalized["decision"] not in {"approve", "edit", "reject"}:
        raise ValueError(f"Unsupported review decision: {normalized['decision']}")
    return normalized


def _apply_reviewer_edits(
    extractions: list[dict[str, Any]],
    edited_extractions: Any,
    edited_risks: Any,
) -> list[dict[str, Any]]:
    updated = {item["clause_id"]: dict(item) for item in extractions}

    if isinstance(edited_extractions, list):
        for patch in edited_extractions:
            clause_id = patch.get("clause_id")
            if clause_id in updated:
                updated[clause_id].update(patch)

    if isinstance(edited_risks, list):
        for patch in edited_risks:
            clause_id = patch.get("clause_id")
            if clause_id in updated:
                if "risk_level" in patch:
                    updated[clause_id]["risk_level"] = patch["risk_level"]
                if "confidence" in patch:
                    updated[clause_id]["confidence"] = patch["confidence"]
                if "reviewer_reason" in patch:
                    updated[clause_id].setdefault("evidence_spans", [])
                    updated[clause_id]["evidence_spans"].append(f"Reviewer: {patch['reviewer_reason']}")

    return [updated[key] for key in sorted(updated.keys())]
