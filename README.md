# agentic-contract-review

An agentic contract review and approval orchestrator built as a portfolio project for a Field/Customer Solutions Engineer role.

The system ingests contracts, extracts clauses via LLM agents, classifies risk against a deterministic policy engine, routes high-risk cases to human reviewers, and tracks measurable business value across the full pilot lifecycle.

## What this demonstrates

- Hands-on Python + API integration + LLM workflow orchestration
- Customer-facing thinking: pilot scope, measurable outcomes, and rollout criteria
- Governance and auditability for enterprise adoption
- Reusable CE patterns instead of one-off demo logic
- Proof-to-Contract evaluation framework: baseline vs. pilot metrics, acceptance gates

## System overview

```text
[Contract Source]
  - Upload / Email / Drive / API
          |
          v
[Ingestion Service]
  - file normalization, metadata enrichment, queue event
          |
          v
[Document Processing]
  - OCR / parsing, section + clause chunking
          |
          v
[Multi-Agent Extraction]
  - Coordinator Agent
      - Extractor Agent      → clause type, obligations, dates, amounts
      - Risk Classifier Agent → risk level + confidence + evidence spans
      - Redline Generator Agent → suggested edits + rationale
          |
          v
[Policy & Risk Engine]
  - deterministic business rules
  - policy packs per customer
  - RAG grounding against policy knowledge base
          |
   +------+------+
   |             |
   v             v
[Auto Path]   [Human Review Queue]
 low-risk      high-risk or low confidence
   |                |
   |                v
   |       [Reviewer Workspace]
   |       - edit risk tags and redlines
   |       - approve / reject / escalate
   |                |
   +---------> [Decision Engine]
                    |
                    v
             [Integrations Layer]
             - CRM update (HubSpot/Salesforce)
             - Ticketing (Jira/Linear)
             - E-sign (DocuSign/PandaDoc)
                    |
                    v
              [Audit + Metrics Store]
              - full decision trace
              - model/prompt/policy versions
              - business KPIs + agent-hours saved
```

## Spec pack

Full design and evaluation documentation is in [`spec/`](./spec/):

1. [`01-project-charter.md`](./spec/01-project-charter.md) — goals, personas, success criteria
2. [`02-system-design.md`](./spec/02-system-design.md) — architecture, governance model, data model
3. [`03-proof-to-contract-eval.md`](./spec/03-proof-to-contract-eval.md) — pilot evaluation framework and acceptance gates
4. [`04-demo-script.md`](./spec/04-demo-script.md) — end-to-end demo flow and Q&A prep
5. [`05-delivery-roadmap.md`](./spec/05-delivery-roadmap.md) — 14-day build plan, risks, CE handoff kit

## Key metrics (pilot targets)

| Metric | Target |
|---|---|
| Median review turnaround | 35%+ reduction |
| High-risk clause recall | >= 90% |
| False-positive rate | < 15% |
| Auto-processed low-risk clauses | >= 60% |
| Agent-hours of capacity unlocked | measured per pilot |
| Full audit trace coverage | 100% |

## Tech stack

- **Python** — FastAPI, Pydantic, asyncio
- **LLM** — Claude (claude-sonnet for extraction, claude-haiku for classification)
- **RAG** — policy knowledge base retrieval via embeddings
- **Integrations** — HubSpot, Jira, DocuSign (sandbox)
- **Storage** — PostgreSQL + S3-compatible blob store
- **Eval** — custom harness comparing baseline vs. pilot runs

## Repo structure

```text
app/
  ingestion/
  parsing/
  agents/
  policy/
  routing/
  integrations/
  audit/
eval/
  datasets/
  scripts/
demo/
  fixtures/
  scripts/
spec/
README.md
```

> Note: the GitHub repository is in the process of being renamed from `agentic-emails` to `agentic-contract-review`.
