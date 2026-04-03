from __future__ import annotations

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
from contract_review_langgraph.graph import graph
from langgraph.types import Command

from api.rate_limit import InMemoryRateLimiter
from api.schemas import (
    ClauseExtractionOut,
    ResumeRequest,
    ResumeResponse,
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
        config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}

        # "provider": "openai" with no OPENAI_API_KEY triggers heuristic fallback.
        # To use a real LLM, set the relevant API key in the environment.
        # TODO: wrap in asyncio.to_thread() if adding real LLM support (blocking call).
        graph.invoke(
            {"contract_path": str(tmp_path), "provider": "openai"},
            config=config,
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

        final_state = graph.get_state(config).values
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
) -> ResumeResponse:
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

    # TODO: wrap in asyncio.to_thread() if adding real LLM support.
    graph.invoke(Command(resume=resume_value), config=config)

    final_state = graph.get_state(config).values
    return ResumeResponse(
        status="completed",
        thread_id=thread_id,
        final_status=final_state.get("final_status", "unknown"),
        route=final_state.get("route", "unknown"),
        extractions=_serialize_extractions(final_state.get("extractions", [])),
        review_decision=final_state.get("review_decision", {}),
    )
