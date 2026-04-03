from pathlib import Path

from contract_review_langgraph.parsing import chunk_into_clauses, compute_file_hash, normalize_text


def test_normalize_text_collapses_spacing() -> None:
    raw = "Alpha   beta\r\n\r\n\r\nGamma"
    assert normalize_text(raw) == "Alpha beta\n\nGamma"


def test_chunk_into_clauses_returns_deterministic_ids() -> None:
    text = "1. Services\n\nVendor provides services.\n\n2. Fees\n\nCustomer pays within 30 days."
    clauses = chunk_into_clauses(text)
    assert [clause.clause_id for clause in clauses] == ["clause-001", "clause-002", "clause-003", "clause-004"]
    assert clauses[0].title == "1. Services"


def test_compute_file_hash_is_stable(tmp_path: Path) -> None:
    file_path = tmp_path / "contract.txt"
    file_path.write_text("hello", encoding="utf-8")
    assert compute_file_hash(file_path) == compute_file_hash(file_path)

