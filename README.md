# agentic-contract-review

A runnable LangGraph Studio MVP for contract review with policy routing, interrupt-based human approval, and local audit/reporting.

The graph is intentionally shaped around 7 business nodes:

1. A contract comes in.
2. The system reads it and breaks it into clauses.
3. AI extracts important details and flags risky language.
4. A rules engine checks company policy.
5. Safe/standard cases move forward automatically.
6. Risky or uncertain cases pause for a human reviewer.
7. Every decision is logged for audit and reporting.

## What this repo is now

This repo started as a spec pack. It now includes a runnable Python LangGraph project that can be opened in LangGraph Studio and demoed locally against contract files on your Mac.

Current MVP scope:

- Local file-path intake for `TXT`, `DOCX`, and text-based `PDF`
- One LangGraph workflow with exactly 7 top-level nodes
- Multi-provider LLM adapter for `OpenAI`, `Gemini`, and `Grok`
- Deterministic policy routing
- Human-in-the-loop approval via LangGraph `interrupt()` with durable local resume
- SQLite + JSONL audit logging
- SQLite-backed LangGraph checkpoints for restart-safe local review recovery
- Markdown run reports under `runtime/reports/`

Deferred from this first pass:

- OCR for scanned PDFs
- CRM / ticketing / e-sign integrations
- Redline generation
- Production auth / multi-tenancy

## Graph shape

```text
START
  |
  v
ingest_contract
  |
  v
parse_and_chunk_clauses
  |
  v
extract_details_and_flag_risk
  |
  v
check_policy_rules
  |--------------------------+
  v                          v
auto_advance_standard_cases  human_review
  |                          |
  +------------->------------+
                |
                v
         audit_and_report
                |
                v
               END
```

## Project structure

```text
contract_review_langgraph/
  graph.py
  checkpointing.py
  nodes.py
  llm.py
  parsing.py
  policies.py
  audit.py
  prompts.py
  state.py
fixtures/
policies/
spec/
tests/
langgraph.json
pyproject.toml
```

## Quick start

1. Create a virtualenv and install dependencies.
2. Copy `.env.example` to `.env` and add at least one API key.
3. Start LangGraph Studio dev mode:

```bash
langgraph dev
```

4. In Studio, run the `contract_review_workflow` graph with input like:

```json
{
  "contract_path": "/Users/your-name/path/to/contract.txt",
  "provider": "openai",
  "policy_pack": "/Users/orbarak/Desktop/or-git/agentic-contract-review/policies/default_policy.yaml",
  "run_label": "local-demo"
}
```

5. By default, `LANGGRAPH_CHECKPOINTER=sqlite`, so interrupted review threads persist to `runtime/audit/checkpoints.sqlite3` and can be resumed after a local process restart.

6. If the graph pauses in `human_review`, resume the same thread with a payload like:

```json
{
  "decision": "edit",
  "edited_extractions": [
    {
      "clause_id": "clause-002",
      "summary": "Reviewer clarified the indemnity obligation."
    }
  ],
  "edited_risks": [
    {
      "clause_id": "clause-002",
      "risk_level": "high",
      "confidence": 0.98,
      "reviewer_reason": "Broad indemnity remained unacceptable."
    }
  ],
  "reviewer_notes": "Escalated risk remained valid.",
  "reviewer_id": "demo-reviewer"
}
```

## API deployment for website demos

This repo also includes a FastAPI wrapper in [`api/main.py`](./api/main.py) for browser-based demos.

Current API surface:

- `POST /api/run`
- `POST /api/resume/{thread_id}`
- `GET /api/runs/{thread_id}`
- `GET /api/pending-reviews`
- `GET /api/health`

If you want to power a public website demo, use the deployment checklist in [`DEPLOYMENT.md`](./DEPLOYMENT.md). It covers:

- local API smoke testing
- Railway deployment
- Vercel `VITE_API_URL` wiring
- CORS setup
- demo-day caveats for interrupt/resume

## Audit outputs

Every run produces local artifacts:

- SQLite DB: `runtime/audit/audit.sqlite3`
- SQLite checkpoints: `runtime/audit/checkpoints.sqlite3`
- JSONL event stream: `runtime/audit/events.jsonl`
- Markdown report: `runtime/reports/<run_id>.md`

## Provider notes

- `openai` uses the OpenAI Chat Completions API.
- `grok` uses an OpenAI-compatible API shape via `https://api.x.ai/v1`.
- `gemini` uses the Google `generateContent` API.
- If the chosen provider is unavailable and `ALLOW_HEURISTIC_FALLBACK=true`, the graph falls back to a deterministic local extractor so the demo can still run.

## Spec pack

The original project framing is still in [`spec/`](./spec/):

1. [`01-project-charter.md`](./spec/01-project-charter.md)
2. [`02-system-design.md`](./spec/02-system-design.md)
3. [`03-proof-to-contract-eval.md`](./spec/03-proof-to-contract-eval.md)
4. [`04-demo-script.md`](./spec/04-demo-script.md)
5. [`05-delivery-roadmap.md`](./spec/05-delivery-roadmap.md)
