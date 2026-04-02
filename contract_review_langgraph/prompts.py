from __future__ import annotations


EXTRACTION_SYSTEM_PROMPT = """You are a contract-review extraction assistant.

Return valid JSON only. Do not wrap the JSON in markdown code fences.
Extract one result for every clause provided. Keep evidence spans short and verbatim.
Use risk levels low, medium, or high only.
"""


def build_extraction_user_prompt(clauses: list[dict]) -> str:
    lines = [
        "Review the contract clauses below and return this JSON shape:",
        '{',
        '  "clauses": [',
        "    {",
        '      "clause_id": "string",',
        '      "clause_type": "string",',
        '      "summary": "string",',
        '      "obligations": ["string"],',
        '      "key_dates": ["string"],',
        '      "amounts": ["string"],',
        '      "jurisdiction": "string or null",',
        '      "risk_level": "low | medium | high",',
        '      "confidence": 0.0,',
        '      "evidence_spans": ["string"]',
        "    }",
        "  ]",
        "}",
        "",
        "Clauses:",
    ]
    for clause in clauses:
        lines.append(f"- {clause['clause_id']} | {clause['title']}")
        lines.append(clause["text"])
        lines.append("")
    return "\n".join(lines)

