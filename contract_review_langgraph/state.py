from __future__ import annotations

from typing import Any, TypedDict


class ContractReviewState(TypedDict, total=False):
    contract_path: str
    provider: str
    policy_pack: str
    run_label: str
    run_id: str
    contract_id: str
    contract_hash: str
    file_type: str
    file_name: str
    raw_text: str
    parse_status: str
    parse_error: str
    clauses: list[dict[str, Any]]
    extractions: list[dict[str, Any]]
    llm_metadata: dict[str, Any]
    policy_results: dict[str, Any]
    policy_pack_name: str
    policy_pack_version: str
    route: str
    review_decision: dict[str, Any]
    audit_events: list[dict[str, Any]]
    final_status: str
    report_path: str
    error: str

