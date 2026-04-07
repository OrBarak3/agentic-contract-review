from __future__ import annotations

import asyncio
import os
import tempfile
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from contract_review_langgraph.config import ensure_runtime_dirs
from contract_review_langgraph.audit import get_run, list_pending_reviews
from contract_review_langgraph.graph import graph
from langgraph.types import Command

from api.rate_limit import InMemoryRateLimiter
from api.schemas import (
    ClauseExtractionOut,
    PendingReviewOut,
    PendingReviewsResponse,
    ResumeRequest,
    ReviewedRunResponse,
    RunCompletedResponse,
    RunInterruptedResponse,
)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_SUFFIXES = {".txt", ".pdf", ".docx", ".md"}

limiter = InMemoryRateLimiter(max_calls=10, window_seconds=60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_runtime_dirs()
    yield


app = FastAPI(title="Contract Review API", version="0.1.0", lifespan=lifespan)

_raw_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:4173",
)
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_interrupt_payload(config: dict[str, Any]) -> dict[str, Any] | None:
    """Returns the interrupt payload if the graph is paused, None if completed."""
    state_snapshot = graph.get_state(config)
    for task in state_snapshot.tasks:
        if task.interrupts:
            return task.interrupts[0].value  # type: ignore[return-value]
    return None


def _get_state_values(config: dict[str, Any]) -> dict[str, Any]:
    return graph.get_state(config).values


def _serialize_extractions(raw: list[dict[str, Any]]) -> list[ClauseExtractionOut]:
    results = []
    for item in raw:
        try:
            results.append(ClauseExtractionOut.model_validate(item))
        except Exception:
            pass
    return results


def _check_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again in a minute.",
        )


# ── routes ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "contract-review-api"}


@app.get("/api/runs/{thread_id}")
async def get_run_status(thread_id: str, request: Request) -> JSONResponse:
    _check_rate_limit(request)

    run = get_run(thread_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"No run found for thread_id={thread_id!r}.")

    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    interrupt_payload = _get_interrupt_payload(config)
    if interrupt_payload is not None:
        return JSONResponse(
            RunInterruptedResponse(
                status="interrupted",
                thread_id=thread_id,
                interrupt_payload=interrupt_payload,
            ).model_dump()
        )

    final_state = _get_state_values(config)
    return JSONResponse(
        ReviewedRunResponse(
            status="completed",
            thread_id=thread_id,
            final_status=final_state.get("final_status", run.get("final_status", "unknown")),
            route=final_state.get("route", run.get("route", "unknown")),
            extractions=_serialize_extractions(final_state.get("extractions", [])),
            review_decision=final_state.get("review_decision", {}),
        ).model_dump()
    )


@app.get("/api/pending-reviews")
async def pending_reviews(request: Request) -> PendingReviewsResponse:
    _check_rate_limit(request)

    items = [
        PendingReviewOut(
            thread_id=item.get("thread_id") or item["run_id"],
            run_id=item["run_id"],
            contract_id=item.get("contract_id"),
            file_name=item.get("file_name"),
            contract_path=item.get("contract_path"),
            provider=item.get("provider"),
            policy_pack=item.get("policy_pack"),
            route=item.get("route"),
            review_status="pending",
            started_at=item["started_at"],
            interrupted_at=item.get("interrupted_at"),
        )
        for item in list_pending_reviews()
    ]
    return PendingReviewsResponse(items=items)


@app.post("/api/run")
async def run_contract(
    request: Request,
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
) -> JSONResponse:
    _check_rate_limit(request)

    if not text and file is None:
        raise HTTPException(status_code=422, detail="Provide either 'text' or 'file'.")
    if text and file is not None:
        raise HTTPException(status_code=422, detail="Provide only one of 'text' or 'file', not both.")

    tmp_path: Path | None = None
    try:
        if text is not None:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(text)
                tmp_path = Path(tmp.name)
        else:
            assert file is not None
            suffix = Path(file.filename or "upload").suffix.lower() or ".txt"
            if suffix not in ALLOWED_SUFFIXES:
                raise HTTPException(
                    status_code=422,
                    detail=f"Unsupported file type: {suffix!r}. Allowed: {', '.join(sorted(ALLOWED_SUFFIXES))}",
                )
            content = await file.read()
            if len(content) > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 5 MB.")
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

        thread_id = str(uuid.uuid4())
        # thread_id and run_id are intentionally the same UUID.
        # LangGraph uses thread_id for checkpoint continuity; the audit DB uses run_id
        # as the primary key. Keeping them equal means one UUID identifies a run everywhere.
        config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}

        # "provider": "openai" with no OPENAI_API_KEY triggers heuristic fallback.
        # To use a real LLM, set the relevant API key in the environment.
        await asyncio.to_thread(
            graph.invoke,
            {
                "contract_path": str(tmp_path),
                "provider": "openai",
                "thread_id": thread_id,
                "run_id": thread_id,
            },
            config,
        )

        interrupt_payload = _get_interrupt_payload(config)
        if interrupt_payload is not None:
            return JSONResponse(
                RunInterruptedResponse(
                    status="interrupted",
                    thread_id=thread_id,
                    interrupt_payload=interrupt_payload,
                ).model_dump()
            )

        final_state = _get_state_values(config)
        return JSONResponse(
            RunCompletedResponse(
                status="completed",
                thread_id=thread_id,
                final_status=final_state.get("final_status", "unknown"),
                route=final_state.get("route", "unknown"),
                extractions=_serialize_extractions(final_state.get("extractions", [])),
                policy_results=final_state.get("policy_results", {}),
            ).model_dump()
        )

    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass


@app.post("/api/resume/{thread_id}")
async def resume_contract(
    thread_id: str,
    body: ResumeRequest,
    request: Request,
) -> ReviewedRunResponse:
    _check_rate_limit(request)

    config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}

    if _get_interrupt_payload(config) is None:
        raise HTTPException(
            status_code=404,
            detail=f"No interrupted graph found for thread_id={thread_id!r}. "
                   "It may have already been resumed or never existed.",
        )

    resume_value = {
        "decision": body.decision,
        "reviewer_notes": body.reviewer_notes,
        "reviewer_id": body.reviewer_id,
        "edited_extractions": body.edited_extractions,
        "edited_risks": body.edited_risks,
    }

    await asyncio.to_thread(graph.invoke, Command(resume=resume_value), config)

    final_state = _get_state_values(config)
    return ReviewedRunResponse(
        status="completed",
        thread_id=thread_id,
        final_status=final_state.get("final_status", "unknown"),
        route=final_state.get("route", "unknown"),
        extractions=_serialize_extractions(final_state.get("extractions", [])),
        review_decision=final_state.get("review_decision", {}),
    )
