from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from contract_review_langgraph.models import PolicyClauseResult, PolicyEvaluation


def load_policy_pack(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def evaluate_policy(extractions: list[dict[str, Any]], policy_pack: dict[str, Any]) -> PolicyEvaluation:
    routing = policy_pack.get("routing", {})
    low_confidence_threshold = float(routing.get("human_review_confidence_threshold", 0.8))
    auto_pass_threshold = float(routing.get("auto_pass_confidence_threshold", 0.9))
    blocked_clause_types = set(routing.get("blocked_clause_types", []))
    required_fields = set(routing.get("required_fields", ["clause_type", "risk_level", "summary"]))

    overall_reasons: list[str] = []
    clause_results: list[PolicyClauseResult] = []
    auto_pass_eligible = True

    for extraction in extractions:
        reasons: list[str] = []
        clause_type = extraction.get("clause_type", "")
        confidence = float(extraction.get("confidence", 0))
        risk_level = extraction.get("risk_level", "medium")

        if confidence < low_confidence_threshold:
            reasons.append(f"confidence_below_threshold:{confidence:.2f}")
        if clause_type in blocked_clause_types:
            reasons.append(f"blocked_clause_type:{clause_type}")
        if risk_level == "high":
            reasons.append("high_risk_clause_detected")

        missing_fields = [field for field in required_fields if not extraction.get(field)]
        if missing_fields:
            reasons.append(f"missing_required_fields:{','.join(sorted(missing_fields))}")

        if confidence < auto_pass_threshold or risk_level != "low":
            auto_pass_eligible = False

        clause_results.append(
            PolicyClauseResult(
                clause_id=extraction["clause_id"],
                requires_human_review=bool(reasons),
                reasons=reasons,
            )
        )
        overall_reasons.extend(reasons)

    if overall_reasons:
        route = "human_review"
    elif auto_pass_eligible and extractions:
        route = "auto_advance"
    else:
        route = "human_review"
        overall_reasons.append("auto_pass_not_eligible")

    deduped_reasons = sorted(set(overall_reasons))
    return PolicyEvaluation(
        route=route,
        reasons=deduped_reasons,
        auto_pass_eligible=(route == "auto_advance"),
        clause_results=clause_results,
    )

