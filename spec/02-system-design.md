# 02 - System Design

## Architecture Overview

```text
[Local Contract File]
  - absolute filesystem path
          |
          v
[LangGraph Node 1: Ingest Contract]
  - validate path
  - hash document
  - initialize run metadata
          |
          v
[LangGraph Node 2: Parse + Chunk Clauses]
  - TXT / MD / DOCX / text-PDF parsing
  - blank-line clause chunking
          |
          v
[LangGraph Node 3: Extract Details + Flag Risk]
  - clause type
  - obligations
  - dates, amounts, jurisdiction
  - confidence + evidence spans
          |
          v
[LangGraph Node 4: Check Policy Rules]
  - deterministic business rules
  - local policy packs
  - route: auto_advance / human_review / audit_only
          |
   +------+------+
   |             |
   v             v
[LangGraph Node 5] [LangGraph Node 6]
[Auto Advance]     [Human Review Interrupt]
 low-risk          approve / edit / reject
 standard cases    in LangGraph Studio
   |                    |
   +----------->--------+
               |
               v
     [LangGraph Node 7: Audit + Report]
       - SQLite run record
       - JSONL event log
       - Markdown report
```

## Current MVP Shape

1. `ingest_contract`
   - Accepts a local file path, validates it, and creates a deterministic contract/run identity.
2. `parse_and_chunk_clauses`
   - Reads `TXT`, `MD`, `DOCX`, and text-based `PDF` files and turns them into clause segments.
   - Normalizes whitespace and splits clauses on paragraph breaks.
3. `extract_details_and_flag_risk`
   - Calls the selected LLM provider and normalizes outputs into a common schema.
   - Falls back to local heuristic extraction if configured and the provider call fails.
4. `check_policy_rules`
   - Applies deterministic routing rules from a local YAML policy pack.
5. `auto_advance_standard_cases`
   - Finalizes clean, high-confidence contracts without human intervention.
6. `human_review`
   - Uses LangGraph `interrupt()` to pause for a reviewer decision and optional edits.
   - Persists the paused thread in a local SQLite checkpoint DB so the review can be resumed after a restart.
7. `audit_and_report`
   - Persists the run and events locally and writes a human-readable report.

## Runtime Interfaces

### Graph input

The current graph expects a payload shaped like:

```json
{
  "contract_path": "/absolute/path/to/contract.txt",
  "provider": "openai",
  "policy_pack": "/absolute/path/to/policies/default_policy.yaml",
  "thread_id": "optional-thread-id",
  "run_id": "optional-existing-id",
  "run_label": "optional-label"
}
```

Notes:

- `contract_path` is required.
- `provider` defaults to `openai` when omitted.
- `policy_pack` defaults to `policies/default_policy.yaml` when omitted.
- `thread_id` is optional for Studio/manual runs and is the public API identifier for durable interrupt/resume flows.
- `run_label` is accepted in state but is currently informational only.

### Human review resume payload

When the graph pauses in `human_review`, it currently resumes with:

```json
{
  "decision": "approve | edit | reject",
  "edited_extractions": [],
  "edited_risks": [],
  "reviewer_notes": "string",
  "reviewer_id": "string"
}
```

## Tech Stack

### Language & Runtime
- **Python 3.11+** — minimal Python runtime for local LangGraph development.
- **LangGraph** — graph orchestration, state management, and interrupt/resume for human review.
- **LangGraph Studio / `langgraph dev`** — local graph visualization and operator interaction surface.

### Data Validation & Schemas
- **Pydantic v2** — schema validation for clause extraction, routing outputs, and policy structures.

### LLM Integration
- **OpenAI** — supported through the Chat Completions API.
- **Grok / xAI** — supported through an OpenAI-compatible API shape.
- **Gemini** — supported through Google's `generateContent` API.
- **Provider abstraction** — the graph selects a provider via input config while keeping one normalized extraction schema.
- **Heuristic fallback** — a deterministic local extractor can be used when provider credentials are missing or the API call fails, which keeps the demo runnable.

### Document Parsing
- **`python-docx`** — DOCX ingestion.
- **`pypdf`** — text extraction for selectable-text PDFs.
- **Plain UTF-8 text/markdown files** — simplest demo input path.
- **OCR is deferred** — scanned PDFs are currently routed to manual handling.

### Storage
- **SQLite** — local audit run registry and event storage.
- **SQLite-backed LangGraph checkpointer** — durable local interrupt/resume state under `runtime/audit/checkpoints.sqlite3`.
- **JSONL event log** — append-only, easy-to-inspect execution trace.
- **Markdown reports** — per-run artifacts for demo and review.

### Policy Layer
- **Local YAML policy packs** — versionable routing rules for auto-pass vs human review.
- **Deterministic evaluation** — policy remains the final authority for routing.
- **No retrieval layer yet** — precedent retrieval / RAG is a next-step expansion, not a current MVP feature.

### Testing
- **pytest** — unit tests for parsing, heuristics, and policy routing.
- **Fixture-driven demos** — `fixtures/low_risk_vendor_msa.txt` and `fixtures/high_risk_vendor_msa.txt` cover the happy path and review path during manual runs.

## Governance Model

- AI proposes; policy decides; human approves high-risk outcomes.
- No external side effects are performed in the current MVP.
- Current audit persistence includes:
  - a SQLite `runs` table with run metadata and final status
  - a SQLite `events` table with node-level event payloads
  - a SQLite LangGraph checkpoint database for paused/resumable threads
  - an append-only JSONL event stream
  - a Markdown per-run summary report
- Event payloads include useful execution metadata such as provider/model selection, policy reasons, and reviewer decision details when available.
- Prompt versioning and richer experiment lineage are not yet first-class persisted fields and should be treated as roadmap.

## Contract Data Model (v1)

- `contract_id`
- `contract_path`
- `contract_hash`
- `file_type`
- `clauses[]`
  - `clause_id`
  - `title`
  - `text`
  - `start_char`
  - `end_char`
- `extractions[]`
  - `clause_type`
  - `summary`
  - `obligations`
  - `key_dates`
  - `amounts`
  - `jurisdiction`
  - `risk_level`
  - `confidence`
  - `evidence_spans`
- `policy_results`
- `review_decision`
  - `decision`
  - `edited_extractions`
  - `edited_risks`
  - `reviewer_notes`
  - `reviewer_id`
- `final_status`
- `decision_trace[]` / audit events

## Risk Routing Rules (Example)

1. Route to human review if confidence < 0.80.
2. Route to human review if clause type is allowlisted as blocked by the policy pack, such as `liability`, `indemnity`, or `termination`.
3. Auto-pass only if:
   - confidence >= 0.90
   - no high-risk clause found
   - all required fields extracted
   - policy checks pass

## Roadmap Expansions

- Retrieval grounding against approved clauses and policy precedents.
- CRM (e.g., Salesforce/HubSpot): push contract status + risk summary.
- Ticketing (e.g., Jira/Linear/Zendesk): create review task.
- E-sign (e.g., DocuSign/PandaDoc): send approved draft.
- Redline generation as a dedicated post-extraction step.

## Failure Handling

- Model/API failure: fall back to the heuristic extractor when enabled, otherwise fail closed into audit.
- Parser failure: mark document as `needs_manual_parse`.
- Missing policy or invalid policy pack: fail closed into audit.
- Missing or invalid input path: fail closed into audit with a run record and error event.
- Validation failure: block action and require reviewer intervention.
