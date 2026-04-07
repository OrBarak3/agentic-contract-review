from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from contract_review_langgraph.checkpointing import create_checkpointer
from contract_review_langgraph.nodes import (
    audit_and_report,
    auto_advance_standard_cases,
    check_policy_rules,
    extract_details_and_flag_risk,
    human_review,
    ingest_contract,
    parse_and_chunk_clauses,
)
from contract_review_langgraph.state import ContractReviewState


def _after_ingest(state: ContractReviewState) -> str:
    if state.get("final_status") == "failed":
        return "audit_and_report"
    return "parse_and_chunk_clauses"


def _after_parse(state: ContractReviewState) -> str:
    if state.get("parse_status") != "parsed":
        return "audit_and_report"
    return "extract_details_and_flag_risk"


def _after_policy(state: ContractReviewState) -> str:
    if state.get("route") == "auto_advance":
        return "auto_advance_standard_cases"
    if state.get("route") == "human_review":
        return "human_review"
    return "audit_and_report"


def _build_state_graph() -> StateGraph:
    builder = StateGraph(ContractReviewState)
    builder.add_node("ingest_contract", ingest_contract)
    builder.add_node("parse_and_chunk_clauses", parse_and_chunk_clauses)
    builder.add_node("extract_details_and_flag_risk", extract_details_and_flag_risk)
    builder.add_node("check_policy_rules", check_policy_rules)
    builder.add_node("auto_advance_standard_cases", auto_advance_standard_cases)
    builder.add_node("human_review", human_review)
    builder.add_node("audit_and_report", audit_and_report)

    builder.add_edge(START, "ingest_contract")
    builder.add_conditional_edges("ingest_contract", _after_ingest)
    builder.add_conditional_edges("parse_and_chunk_clauses", _after_parse)
    builder.add_edge("extract_details_and_flag_risk", "check_policy_rules")
    builder.add_conditional_edges("check_policy_rules", _after_policy)
    builder.add_edge("auto_advance_standard_cases", "audit_and_report")
    builder.add_edge("human_review", "audit_and_report")
    builder.add_edge("audit_and_report", END)
    return builder


def build_graph(*, checkpointer=None, checkpointer_kind: str | None = None, checkpoint_path=None):
    saver = checkpointer
    if saver is None:
        saver = create_checkpointer(
            kind=checkpointer_kind,
            checkpoint_path=checkpoint_path,
        )
    return _build_state_graph().compile(checkpointer=saver)


graph = build_graph()
