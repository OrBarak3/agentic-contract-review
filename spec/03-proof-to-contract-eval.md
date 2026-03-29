# 03 - Proof-to-Contract Evaluation Spec

## Purpose

Define how to prove technical and business value in a pilot so stakeholders can confidently move from proof to contract.

## Pilot Hypotheses

1. The workflow reduces contract review cycle time by at least 35%.
2. Risk detection quality is high enough for controlled production usage.
3. Human review load decreases without losing governance quality.

## Evaluation Dataset

- 100 to 300 historical contracts (mixed templates and counterparties).
- Include a labeled subset with human-reviewed clause risk annotations.
- Split:
  - 60% calibration
  - 20% validation
  - 20% holdout

## Measurement Framework

### Quality Metrics

- High-risk clause recall
  - Target: >= 0.90
- High-risk precision
  - Target: >= 0.80
- Required field extraction F1
  - Target: >= 0.92
- Redline acceptance rate (human accepted with minor/no edits)
  - Target: >= 0.60 in pilot

### Workflow Metrics

- Median review turnaround time
  - Target: 35%+ improvement from baseline
- Throughput (contracts/week/reviewer)
  - Target: 30%+ uplift
- Human escalation rate
  - Target: 25% to 50% (healthy during pilot, should trend down with tuning)

### Reliability Metrics

- P95 end-to-end latency per contract
  - Target: < 5 minutes (pilot expectation)
- Processing success rate
  - Target: >= 98%
- Integration delivery success
  - Target: >= 99% with retries

## Baseline vs Pilot Design

1. Baseline: existing manual review process over 2 to 4 weeks.
2. Pilot: same contract categories through the orchestrator with human oversight.
3. Compare:
   - cycle time
   - error/risk misses
   - reviewer effort hours
   - stakeholder confidence (qualitative rubric)

## Acceptance Gates

Pilot can move toward production rollout only if all are true:

1. No critical governance violations in holdout.
2. High-risk recall threshold met.
3. Business time-saving threshold met.
4. Stakeholder sign-off from legal + business owner.
5. Incident playbook tested in at least one tabletop run.

## Reporting Pack (for customer/recruiter narrative)

- One-page KPI scorecard (baseline vs pilot).
- Top 10 error patterns and mitigations.
- Policy exceptions log.
- Recommended rollout scope and guardrails.

## Experiment Backlog (Post-Pilot)

- Policy-pack customization by business unit.
- Clause-level retrieval grounding improvements.
- Reviewer UX tuning for faster approvals.
- Active learning loop from accepted/rejected redlines.
