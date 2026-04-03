# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Python LangGraph contract review workflow with interrupt-based human approval, policy-driven routing, and local SQLite/JSONL audit. Entrypoint: `contract_review_langgraph/graph.py:graph`. Run in LangGraph Studio.

## Environment setup

```bash
pip install -e ".[dev]"   # install package + dev deps
cp .env.example .env      # then fill in at least one provider API key
```

Required env vars: `DEFAULT_PROVIDER` (`openai` | `gemini` | `grok`) and the matching API key. See `.env.example` for full list.

## Running

```bash
langgraph dev    # start LangGraph Studio dev server
pytest tests/   # run the test suite
```

## Governance model — do not break

**AI proposes, policy decides, human approves.** This is the architectural invariant.

- Keep routing rules in `policies/default_policy.yaml` and Python code (`policies.py`), never in prompts.
- LLM confidence scores inform routing thresholds; they never override policy rules directly.
- Do not remove or weaken audit logging. Every node transition and human review decision must be written to SQLite + JSONL. Audit events are append-only; the `runs` table upserts for idempotency.

## LangGraph state behavior

Nodes return **partial state dicts** that are merged into `ContractReviewState` — they do not replace it. `ContractReviewState` uses `total=False`. Returning `{"route": "human_review"}` does not erase other state fields.

`human_review` uses `langgraph.types.interrupt(payload)` to pause the graph synchronously. Resume the same thread ID in Studio to continue.

## LLM providers

- Provider names are exact strings: `"openai"`, `"gemini"`, `"grok"`. Typos fail at extraction time, not init.
- Model IDs come from env vars (`OPENAI_MODEL`, `GEMINI_MODEL`, `GROK_MODEL`). Do not hardcode them.
- If `ALLOW_HEURISTIC_FALLBACK=true` and a provider call fails, a local keyword/regex extractor runs instead (sets confidence to 0.5, which typically triggers human review). Keep this path working when changing extraction logic.

## File type support

Supported: `.txt`, `.md`, `.docx`, text-based `.pdf`. Scanned PDFs raise `UnsupportedDocumentError("pdf_has_no_selectable_text")` — no OCR, by design.

## Code conventions

- Small, focused modules (~100 lines). No new class hierarchies or abstractions unless clearly needed.
- Type hints on all functions. Pydantic models for validated data (not raw dicts).
- Clause IDs are deterministic (`clause-001`, `clause-002`, …). Changing parsing will shift IDs and break audit trail continuity — document if intentional.
- Policy packs are `dict[str, Any]` (YAML-loaded, no schema validation). This is intentional flexibility; don't add schema enforcement without discussion.

## Scope — deferred by design

Do not add without explicit ask: OCR, CRM/ticketing integration, redline generation, auth, multi-tenancy, retrieval/RAG. These are explicitly deferred in `REVIEW.md` and `spec/`.

## Documentation discipline

If you change graph structure, supported file types, providers, or audit behavior: update `README.md` and the relevant file in `spec/` in the same change. `REVIEW.md` and `spec/*` are product-facing.
