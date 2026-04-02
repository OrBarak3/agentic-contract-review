from contract_review_langgraph.policies import evaluate_policy


def test_policy_routes_high_risk_clauses_to_human_review() -> None:
    evaluation = evaluate_policy(
        [
            {
                "clause_id": "clause-001",
                "clause_type": "liability",
                "summary": "Unlimited liability applies.",
                "risk_level": "high",
                "confidence": 0.95,
            }
        ],
        {
            "routing": {
                "human_review_confidence_threshold": 0.8,
                "auto_pass_confidence_threshold": 0.9,
                "blocked_clause_types": ["liability"],
                "required_fields": ["clause_type", "risk_level", "summary"],
            }
        },
    )
    assert evaluation.route == "human_review"
    assert "blocked_clause_type:liability" in evaluation.reasons


def test_policy_auto_passes_clean_low_risk_clauses() -> None:
    evaluation = evaluate_policy(
        [
            {
                "clause_id": "clause-001",
                "clause_type": "payment",
                "summary": "Invoice due in 30 days.",
                "risk_level": "low",
                "confidence": 0.95,
            }
        ],
        {
            "routing": {
                "human_review_confidence_threshold": 0.8,
                "auto_pass_confidence_threshold": 0.9,
                "blocked_clause_types": ["liability"],
                "required_fields": ["clause_type", "risk_level", "summary"],
            }
        },
    )
    assert evaluation.route == "auto_advance"
    assert evaluation.auto_pass_eligible is True

