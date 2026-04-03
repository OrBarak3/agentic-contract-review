from contract_review_langgraph.llm import heuristic_extract_clause


def test_heuristic_marks_indemnity_as_high_risk() -> None:
    extraction = heuristic_extract_clause(
        {
            "clause_id": "clause-001",
            "title": "Indemnity",
            "text": "Customer shall indemnify and hold harmless Vendor from all claims.",
        }
    )
    assert extraction["clause_type"] == "indemnity"
    assert extraction["risk_level"] == "high"
    assert extraction["confidence"] >= 0.9

