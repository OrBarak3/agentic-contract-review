from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ClauseExtractionOut(BaseModel):
    clause_id: str
    clause_type: str
    summary: str
    obligations: list[str] = Field(default_factory=list)
    key_dates: list[str] = Field(default_factory=list)
    amounts: list[str] = Field(default_factory=list)
    jurisdiction: str | None = None
    risk_level: Literal["low", "medium", "high"]
    confidence: float
    evidence_spans: list[str] = Field(default_factory=list)


class RunCompletedResponse(BaseModel):
    status: Literal["completed"] = "completed"
    thread_id: str
    final_status: str
    route: str
    extractions: list[ClauseExtractionOut]
    policy_results: dict[str, Any]


class RunInterruptedResponse(BaseModel):
    status: Literal["interrupted"] = "interrupted"
    thread_id: str
    interrupt_payload: dict[str, Any]


class ResumeRequest(BaseModel):
    decision: Literal["approve", "edit", "reject"]
    reviewer_notes: str = ""
    reviewer_id: str = "portfolio-demo"
    edited_extractions: list[dict[str, Any]] = Field(default_factory=list)
    edited_risks: list[dict[str, Any]] = Field(default_factory=list)


class ResumeResponse(BaseModel):
    status: Literal["completed"] = "completed"
    thread_id: str
    final_status: str
    route: str
    extractions: list[ClauseExtractionOut]
    review_decision: dict[str, Any]
