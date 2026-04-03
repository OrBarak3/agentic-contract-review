# 01 - Project Charter

## Project Name

Agentic Contract Review + Approval Orchestrator

## Goal

Show the ability to design, build, validate, and present a production-style AI workflow that sits at the intersection of engineering and customer outcomes.

## Current Implementation Status

The current repo includes a runnable LangGraph Studio MVP. It covers:

1. Local contract intake by filesystem path.
2. Parsing and clause chunking for `TXT`, `MD`, `DOCX`, and selectable-text `PDF` documents.
3. Provider-backed extraction for `openai`, `gemini`, and `grok`, with heuristic fallback available for demo resilience.
4. Deterministic policy routing from local YAML policy packs.
5. Human review via LangGraph interrupt/resume with `approve`, `edit`, or `reject`.
6. Local audit logging and Markdown reporting.

The broader product vision below remains valid, but some items are still roadmap rather than implemented MVP features.

## Why This Project Fits the Role

- Demonstrates hands-on Python + API integration + LLM workflow orchestration.
- Demonstrates customer-facing thinking: pilot scope, measurable outcomes, and rollout criteria.
- Demonstrates governance and auditability for enterprise adoption.
- Demonstrates reusable CE patterns instead of one-off demo logic.

## Problem Statement

Legal and procurement teams spend too long reviewing repetitive contract language. Manual review creates bottlenecks, inconsistent risk decisions, and weak visibility into cycle time, clause-level risk, and how many reviewer agent-hours are consumed by repeatable work.

## Product Outcome

Given a contract document, the system should:

1. Parse and extract key clauses and metadata.
2. Classify clause risk against policy rules.
3. Route high-risk or low-confidence outputs to human review.
4. Log every decision for audit and quality evaluation.
5. Optionally expand later into redline generation and downstream system actions.

## In Scope

- Contract ingestion from local files for the MVP.
- Clause extraction + risk classification.
- Human-in-the-loop review step.
- Approval/decision workflow.
- Local audit trail and run reports.
- Policy packs that can be reused across demos/customers.
- Fixture-based low-risk and high-risk demo runs.

## Out of Scope (v1)

- Full multi-tenant authorization model.
- Deep custom training/fine-tuning pipeline.
- Full legal knowledge graph.
- OCR for scanned PDFs.
- External CRM / ticketing / e-sign integrations.
- Redline generation.
- Hosted upload flows or email/drive ingestion.
- Production-grade front-end polish beyond demo quality.

## Personas

- Legal Ops Manager: wants faster review without increased risk.
- Procurement Manager: wants faster turnaround and predictable SLAs.
- Solutions Engineer / Customer Engineer: configures policies and validates business impact with stakeholders.

## User Stories

1. As a reviewer, I want high-risk clauses pre-flagged so I can focus on critical issues.
2. As a legal manager, I want a clear rationale for each risk flag so decisions are explainable.
3. As a pilot owner, I want baseline vs pilot metrics, including agent-hours of capacity unlocked, to justify rollout.
4. As a SE/CE, I want reusable templates and policy packs for new customers.

## Success Criteria (Pilot)

- Median review turnaround reduced by at least 35%.
- Agent-hours of review capacity unlocked by at least 6 hours/week/reviewer.
- High-risk clause recall at least 90%.
- False-positive risk flag rate below 15%.
- At least 60% of low-risk clauses auto-processed with human spot checks.
- Full audit trace on 100% of decisions.

## Non-Functional Requirements

- Secure handling of documents (PII-safe logging strategy).
- Deterministic policy layer for final approval routing.
- Retry and fallback behavior for model/API failures.
- Reproducibility (versioned prompts, model IDs, and policy bundles).
- Demoability in LangGraph Studio with a reviewer interrupt path that can be resumed deterministically.
- Local inspectability of artifacts so a reviewer can trace a run without extra infrastructure.
