# 02 - System Design

## Architecture Overview

```text
[Contract Source]
  - Upload UI / Email / Drive / API
          |
          v
[Ingestion Service]
  - file normalization
  - metadata enrichment
  - queue event
          |
          v
[Document Processing]
  - OCR / parsing
  - section + clause chunking
          |
          v
[LLM Extraction Agent]
  - clause type
  - obligations
  - dates, amounts, jurisdiction
  - confidence + evidence spans
          |
          v
[Policy & Risk Engine]
  - deterministic business rules
  - policy packs by customer
  - risk level: low / medium / high
          |
   +------+------+
   |             |
   v             v
[Auto Path]   [Human Review Queue]
 low-risk      high-risk or low confidence
 allowed       requires legal approval
 actions         |
   |             v
   |       [Reviewer Workspace]
   |       - edit risk and redlines
   |       - approve/reject/escalate
   |             |
   +-------> [Decision Engine]
               |
               v
        [Integrations Layer]
        - CRM update
        - ticket status
        - e-sign initiation
               |
               v
         [Audit + Metrics Store]
         - decision trace
         - model/prompt versions
         - business KPIs
```

## Core Services

1. Ingestion Service
   - Handles document intake and metadata.
   - Emits idempotent processing jobs.
2. Parsing Service
   - Converts files to normalized text with section boundaries.
3. LLM Extraction Agent
   - Produces structured JSON with evidence and confidence.
4. Policy & Risk Engine
   - Final authority for allowed actions and routing logic.
5. Reviewer Workspace API
   - Exposes tasks and captures reviewer edits/approvals.
6. Integration Adapter Layer
   - Sends updates to external systems via webhooks/API clients.
7. Audit & Metrics Pipeline
   - Stores all states/events for compliance and measurement.
   - Computes business KPIs, including `agent-hours`, defined as reviewer hours avoided by the orchestrator and returned to the team as usable capacity.

## Tech Stack

### Language & Runtime
- **Python 3.11+** — async-native with `asyncio`; standard for LLM tooling ecosystem.

### API Layer
- **FastAPI** — Reviewer Workspace API and Integration Adapter endpoints.
  Chosen over Flask/Django for: native async support, automatic OpenAPI schema generation from Pydantic models, and first-class dependency injection for auth middleware.

### Data Validation & Schemas
- **Pydantic v2** — All data models (`Contract`, `Clause`, `RiskDecision`) are Pydantic models.
  Provides: strict type validation at ingestion boundaries, JSON serialization, and schema export for the audit store.

### LLM Integration
- **Primary model: `claude-opus-4-6` (Anthropic)** — used for clause extraction and redline generation.
  Rationale: 200K context window handles full contract length without chunking; structured output via tool use / JSON mode eliminates post-processing heuristics.
- **Fallback model: `claude-haiku-4-5`** — used on timeout retry path for low-cost re-attempt before human escalation.
- **SDK: Anthropic Python SDK (raw API calls)**, not LangChain.
  Tradeoff: LangChain provides chain abstractions and retriever integrations but adds version instability and abstraction overhead. For a focused extraction pipeline with a single provider, raw SDK calls keep prompt logic explicit and auditable — important for the governance model. LangChain would be reconsidered if the retriever count grows beyond 2.

### Document Parsing
- **pdfplumber** — PDF text + bounding box extraction (used before OCR fallback).
- **pytesseract / Tesseract** — OCR fallback for scanned PDFs.
- **python-docx** — DOCX ingestion.

### Storage
- **PostgreSQL** (via `asyncpg`) — contracts, clauses, decisions, audit trace.
- **Redis** — processing job queue (via `rq`) and reviewer session cache.

### RAG / Policy Knowledge Base
- **Embeddings: `text-embedding-3-small` (OpenAI)** or `voyage-3` — clause chunks embedded at ingestion.
- **Vector store: pgvector** (Postgres extension) — keeps the stack minimal; avoids a separate Pinecone/Weaviate dependency for v1.
- **Retrieval**: risk classifier queries the policy KB to ground flag decisions against past-approved contract language and policy templates, rather than relying solely on deterministic rules.

### Testing
- **pytest + pytest-asyncio** — unit and integration tests.
- **Pydantic model factories** — deterministic test fixtures for clause extraction outputs.

## Governance Model

- AI proposes; policy decides; human approves high-risk outcomes.
- No autonomous external side effects without allowlisted policy pass.
- Every action stores:
  - `model_id`
  - `prompt_version`
  - `policy_pack_version`
  - `input_hash`
  - `decision_reason`
  - `actor` (`system` or user ID)

## Contract Data Model (v1)

- `contract_id`
- `source`
- `customer_id`
- `ingested_at`
- `clauses[]`
  - `clause_id`
  - `clause_type`
  - `text_span`
  - `extracted_fields`
  - `risk_level`
  - `confidence`
  - `evidence`
- `proposed_redlines[]`
- `review_status`
- `final_decision`
- `decision_trace[]`

## Risk Routing Rules (Example)

1. Route to human review if confidence < 0.80.
2. Route to human review if clause is `liability`, `indemnity`, or `termination` and deviation from policy template > threshold.
3. Auto-pass only if:
   - confidence >= 0.90
   - no high-risk clause found
   - all required fields extracted
   - policy checks pass

## Integration Targets (Minimum Demo Set)

- CRM (e.g., Salesforce/HubSpot): push contract status + risk summary.
- Ticketing (e.g., Jira/Linear/Zendesk): create review task.
- E-sign (e.g., DocuSign/PandaDoc): send approved draft.

## Failure Handling

- Model timeout: retry with capped backoff, then fallback model.
- Parser failure: mark document as `needs_manual_parse`.
- Integration error: move to retry queue and expose operator alert.
- Validation failure: block action and require reviewer intervention.
