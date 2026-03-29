# 05 - 14-Day Delivery Roadmap

## Build Objective

Deliver a portfolio-grade MVP with working integrations, governance controls, and pilot-ready metrics.

## Assumptions

- Single developer.
- Python-first backend.
- Simple web UI or notebook-based reviewer interface.
- Mock or sandbox API credentials are available for integrations.

## Week 1 (Core Workflow)

### Day 1-2: Foundations

- Set up repo structure and config management.
- Define core schemas (contract, clause, decision trace).
- Implement ingestion endpoint and queue stub.

### Day 3-4: Extraction + Policy

- Build parser/OCR pipeline for input docs.
- Implement LLM extraction pipeline with typed schema validation.
- Implement policy/risk rules and routing logic.

### Day 5-6: Human-in-the-Loop

- Build reviewer queue API and minimal interface.
- Capture reviewer edits and final decisions.
- Persist full audit trace with version metadata.

### Day 7: Integration Adapters

- Integrate CRM update flow.
- Integrate ticketing workflow.
- Add retry/error handling.

## Week 2 (Proof + Presentation)

### Day 8-9: Evaluation Harness

- Create labeled eval dataset format.
- Implement baseline vs pilot metric scripts.
- Generate KPI summary outputs.

### Day 10-11: Reliability + Hardening

- Add fallback model path and timeout handling.
- Add idempotency and duplicate event protection.
- Add structured logging and alert hooks.

### Day 12: Demo Surface

- Build simple dashboard or CLI report:
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

## Risks and Mitigations

1. Risk: extraction quality varies by contract format.
   - Mitigation: add parser normalization and confidence-based routing.
2. Risk: over-reliance on model confidence.
   - Mitigation: policy engine as mandatory gate before actions.
3. Risk: integration instability.
   - Mitigation: retry queue, idempotency keys, dead-letter handling.
4. Risk: weak recruiter narrative.
   - Mitigation: always present baseline vs pilot metrics, not only architecture.

## Definition of Done

- End-to-end contract flow works on sample set.
- High-risk clauses correctly route to human review.
- At least two external system integrations are demonstrated.
- Audit trail captures decision lineage.
- Pilot KPI report can be generated from run data.
