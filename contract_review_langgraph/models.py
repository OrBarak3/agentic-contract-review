from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]
Route = Literal["auto_advance", "human_review", "audit_only"]
FinalStatus = Literal[
    "approved_automatically",
    "approved_by_reviewer",
    "approved_with_edits",
    "rejected_by_reviewer",
    "needs_manual_parse",
    "failed",
]


class ClauseSegment(BaseModel):
    clause_id: str
    title: str
    text: str
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)


class ClauseExtraction(BaseModel):
    clause_id: str
    clause_type: str
    summary: str
    obligations: list[str] = Field(default_factory=list)
    key_dates: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    jurisdiction: str | None = None
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_spans: list[str] = Field(default_factory=list)


class PolicyClauseResult(BaseModel):
    clause_id: str
    requires_human_review: bool = False
    reasons: list[str] = Field(default_factory=list)


class PolicyEvaluation(BaseModel):
    route: Route
    reasons: list[str] = Field(default_factory=list)
    auto_pass_eligible: bool = False
    clause_results: list[PolicyClauseResult] = Field(default_factory=list)

