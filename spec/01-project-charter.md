# 01 - Project Charter

## Project Name

Agentic Contract Review + Approval Orchestrator

## Goal

Show the ability to design, build, validate, and present a production-style AI workflow that sits at the intersection of engineering and customer outcomes.

## Why This Project Fits the Role

- Demonstrates hands-on Python + API integration + LLM workflow orchestration.
- Demonstrates customer-facing thinking: pilot scope, measurable outcomes, and rollout criteria.
- Demonstrates governance and auditability for enterprise adoption.
- Demonstrates reusable CE patterns instead of one-off demo logic.

## Problem Statement

Legal and procurement teams spend too long reviewing repetitive contract language. Manual review creates bottlenecks, inconsistent risk decisions, and weak visibility into cycle time and clause-level risk.

## Product Outcome

Given a contract document, the system should:

1. Parse and extract key clauses and metadata.
2. Classify clause risk against policy rules.
3. Generate suggested redlines and rationale.
4. Route high-risk or low-confidence outputs to human review.
5. Log every decision for audit and quality evaluation.

## In Scope

- Contract ingestion (upload + webhook source).
- Clause extraction + risk classification.
- Suggested redline generation.
- Human-in-the-loop review queue.
- Approval/decision workflow.
- Integrations (at least 2): CRM/helpdesk/ticketing/e-sign.
- Metrics dashboard for pilot outcomes.

## Out of Scope (v1)

- Full multi-tenant authorization model.
- Deep custom training/fine-tuning pipeline.
- Full legal knowledge graph.
- Production-grade front-end polish beyond demo quality.

## Personas

- Legal Ops Manager: wants faster review without increased risk.
- Procurement Manager: wants faster turnaround and predictable SLAs.
- Solutions Engineer / Customer Engineer: configures policies and validates business impact with stakeholders.

## User Stories

1. As a reviewer, I want high-risk clauses pre-flagged so I can focus on critical issues.
2. As a legal manager, I want a clear rationale for each risk flag so decisions are explainable.
3. As a pilot owner, I want baseline vs pilot metrics to justify rollout.
4. As a SE/CE, I want reusable templates and policy packs for new customers.

## Success Criteria (Pilot)

- Median review turnaround reduced by at least 35%.
- High-risk clause recall at least 90%.
- False-positive risk flag rate below 15%.
- At least 60% of low-risk clauses auto-processed with human spot checks.
- Full audit trace on 100% of decisions.

## Non-Functional Requirements

- Secure handling of documents (PII-safe logging strategy).
- Deterministic policy layer for final approval routing.
- Retry and fallback behavior for model/API failures.
- Reproducibility (versioned prompts, model IDs, and policy bundles).
