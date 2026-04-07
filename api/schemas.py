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


class ReviewedRunResponse(BaseModel):
    """Returned by GET /api/runs/{thread_id} and POST /api/resume/{thread_id}.

    Represents a completed run that may have gone through human review.
    review_decision is empty dict when no human input occurred.
    """

    status: Literal["completed"] = "completed"
    thread_id: str
    final_status: str
    route: str
    extractions: list[ClauseExtractionOut] = Field(default_factory=list)
    review_decision: dict[str, Any] = Field(default_factory=dict)


class PendingReviewOut(BaseModel):
    thread_id: str
    run_id: str
    contract_id: str | None = None
    file_name: str | None = None
    contract_path: str | None = None
    provider: str | None = None
    policy_pack: str | None = None
    route: str | None = None
    review_status: Literal["pending"]
    started_at: str
    interrupted_at: str | None = None


class PendingReviewsResponse(BaseModel):
    items: list[PendingReviewOut] = Field(default_factory=list)


class ResumeRequest(BaseModel):
    decision: Literal["approve", "edit", "reject"]
    reviewer_notes: str = ""
    reviewer_id: str = "portfolio-demo"
    edited_extractions: list[dict[str, Any]] = Field(default_factory=list)
    edited_risks: list[dict[str, Any]] = Field(default_factory=list)


