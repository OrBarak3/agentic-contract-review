# AGENTS.md

This repo contains a runnable LangGraph Studio MVP for contract review. Keep the implementation demoable, local-first, and honest about what is already built versus what is still roadmap.

## Working principles

- Keep the top-level graph aligned to the current 7 business nodes unless a change clearly improves the demo story.
- Prefer small, explicit Python modules over framework-heavy abstractions.
- Preserve the governance model: AI proposes, policy decides, human approves risky or uncertain outcomes.
- Treat `README.md`, `REVIEW.md`, and everything in `spec/` as product-facing artifacts. If behavior changes, update the docs in the same task.

## Current implementation truth

- The LangGraph entrypoint is [`contract_review_langgraph/graph.py`](./contract_review_langgraph/graph.py) and is exposed in `langgraph.json` as `contract_review_workflow`.
- Node logic lives in [`contract_review_langgraph/nodes.py`](./contract_review_langgraph/nodes.py).
- Shared schemas live in [`contract_review_langgraph/models.py`](./contract_review_langgraph/models.py) and [`contract_review_langgraph/state.py`](./contract_review_langgraph/state.py).
- Provider-specific API logic lives in [`contract_review_langgraph/llm.py`](./contract_review_langgraph/llm.py) behind a common extraction interface.
- Parsing logic lives in [`contract_review_langgraph/parsing.py`](./contract_review_langgraph/parsing.py).
- Policy loading and deterministic routing live in [`contract_review_langgraph/policies.py`](./contract_review_langgraph/policies.py) and [`policies/default_policy.yaml`](./policies/default_policy.yaml).
- Audit/report writing lives in [`contract_review_langgraph/audit.py`](./contract_review_langgraph/audit.py).

## Demo and product boundaries

- Current MVP intake is a local filesystem path, not upload, email, or hosted ingestion.
- Current MVP supports UTF-8 `TXT`, `MD`, `DOCX`, and selectable-text `PDF`.
- Scanned-PDF OCR is deferred. Non-parseable files route to manual handling rather than OCR.
- Current supported extraction providers are `openai`, `gemini`, and `grok`.
- If provider calls fail and `ALLOW_HEURISTIC_FALLBACK=true`, extraction falls back to a deterministic local heuristic path so the demo can still run.
- Human review is implemented through LangGraph `interrupt()` and resume, which is acceptable for the portfolio demo.
- External integrations, retrieval grounding, and redline generation are roadmap items unless explicitly implemented in code.

## Audit and runtime expectations

- Runtime artifacts should remain local-first and easy to inspect:
  - SQLite runs/events store at `runtime/audit/audit.sqlite3`
  - JSONL event stream at `runtime/audit/events.jsonl`
  - Markdown reports at `runtime/reports/<run_id>.md`
- Keep audit behavior fail-closed for risky paths and errors.
- The current audit model records run metadata and node events; do not document richer lineage than the code actually persists.

## Fixtures and tests

- Demo fixtures live in `fixtures/`, especially:
  - `fixtures/low_risk_vendor_msa.txt`
  - `fixtures/high_risk_vendor_msa.txt`
- Tests currently cover parsing, heuristic extraction, and policy routing under `tests/`.
- If you change routing, parsing, extraction normalization, or audit behavior, update or extend the relevant tests in the same task.

## Safe change rules

- Do not remove audit logging or human review gates from risky flows.
- Do not let provider-specific behavior leak into the graph state shape.
- Keep deterministic routing rules in policy files and policy evaluation code, not hidden inside prompts.
- If a change affects supported file types, providers, runtime artifacts, or the public demo flow, update `README.md`, `REVIEW.md`, and the relevant files in `spec/`.
- If a change affects the Studio run/resume flow, update the quick-start example in `README.md` and the demo script in `spec/04-demo-script.md`.
