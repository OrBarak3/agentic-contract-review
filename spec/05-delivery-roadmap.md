# 05 - 14-Day Delivery Roadmap

## Build Objective

Deliver a portfolio-grade MVP with governance controls and pilot-ready metrics, then expand it into a more customer-complete workflow.

## Current Status

The repo now has the core MVP implemented:

- LangGraph Studio graph with 7 business nodes
- local file-path intake
- parsing and clause chunking for `TXT`, `MD`, `DOCX`, and selectable-text `PDF`
- provider-backed extraction with heuristic fallback
- deterministic policy routing
- Studio-based human review interrupt
- SQLite / JSONL / Markdown audit outputs
- fixture contracts and unit tests for key core behaviors

The roadmap below should be read as the next steps after that MVP baseline.

## Assumptions

- Single developer.
- Python-first backend.
- LangGraph Studio is the primary operator surface for the MVP.
- Mock or sandbox API credentials are available for provider testing.

## Next Build Window (Core Expansion)

### Day 1-2: Foundations

- Tighten graph state schemas and add richer fixture coverage.
- Add `.env` presets and provider-specific setup notes.
- Improve run metadata and audit query ergonomics.

### Day 3-4: Extraction + Policy

- Improve clause chunking quality for real-world contract formatting.
- Add retrieval grounding against approved clauses or policy exemplars.
- Extend policy packs with customer-specific thresholds and exceptions.

### Day 5-6: Human-in-the-Loop

- Add a lightweight reviewer UI or FastAPI wrapper over the interrupt/resume flow.
- Capture richer reviewer annotations and override reasons.
- Add audit views for comparing model output versus reviewer edits.

### Day 7: Integrations

- Add one post-decision integration stub, ideally a CRM-style status sync.
- Add retry/error handling around that adapter.
- Document which integration contracts are reusable for the next customer.

## Following Build Window (Proof + Presentation)

### Day 8-9: Evaluation Harness

- Create labeled eval dataset format.
- Implement baseline vs pilot metric scripts.
- Generate KPI summary outputs.

### Day 10-11: Reliability + Hardening

- Add provider-specific retry and timeout behavior.
- Add idempotency and duplicate event protection.
- Add policy-pack validation and better failure reporting.
- Decide whether to persist prompt/version metadata for stronger audit lineage.

### Day 12: Demo Surface

- Improve the Studio demo surface and add a lightweight external viewer if needed:
  - contract statuses
  - risk routing outcomes
  - KPI scorecard

### Day 13: Demo Rehearsal

- Run full end-to-end script twice.
- Capture screenshots and backup artifacts.
- Prepare answers for governance and failure scenarios.

### Day 14: Packaging

- Final README and architecture diagram.
- 2 to 3 minute project walkthrough video (optional but high value).
- One-page "Proof-to-Contract" summary PDF/MD.

## Recommended Repo Structure

```text
project/
  contract_review_langgraph/
    graph.py
    nodes.py
    parsing.py
    llm.py
    policies.py
    audit.py
  fixtures/
  policies/
  tests/
  spec/
  README.md
```

## Risks and Mitigations

1. Risk: extraction quality varies by contract format.
   - Mitigation: add parser normalization and confidence-based routing.
2. Risk: over-reliance on model confidence.
   - Mitigation: policy engine as mandatory gate before actions.
3. Risk: LangGraph Studio demo is strong for technical audiences but not enough for end-user workflow realism.
   - Mitigation: add a thin reviewer-facing UI or wrapper API as the next layer.
4. Risk: weak recruiter narrative.
   - Mitigation: always present baseline vs pilot metrics, not only architecture.
5. Risk: MVP/docs drift.
   - Mitigation: update the spec pack and README whenever the implemented surface changes.

## Definition of Done

- End-to-end contract flow works on sample set.
- High-risk clauses correctly route to human review.
- Audit trail captures decision lineage.
- Pilot KPI report can be generated from run data.
- One next-step expansion is added beyond the MVP, such as retrieval grounding or a post-decision integration.
- Docs remain aligned with the actual implemented scope.

## CE Handoff Kit

Document these items for the next engineer or customer-facing teammate:

- Which policy-pack fields are customer-specific versus reusable defaults
- Which providers are supported and how to configure them
- Which fixtures best demonstrate low-risk and high-risk behavior
- What the current MVP does not yet do, so customers are not over-promised
