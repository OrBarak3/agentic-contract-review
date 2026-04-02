# Contract Review Orchestrator Spec Pack

This folder contains the design and narrative docs for the contract review portfolio project.

The repo now includes a runnable LangGraph Studio MVP, so these docs should be read as:

- the original product framing,
- the current MVP boundaries,
- and the next-step roadmap beyond the current implementation.

## Read Order

1. `01-project-charter.md` - What we are building, why it matters, and success criteria.
2. `02-system-design.md` - End-to-end architecture, governance model, and integration points.
3. `03-proof-to-contract-eval.md` - Pilot evaluation framework and contract-readiness thresholds.
4. `04-demo-script.md` - Recruiter/customer-ready demo flow.
5. `05-delivery-roadmap.md` - Next-step roadmap, risks, and deliverables.

## Project One-Liner

Build an agentic contract review and approval orchestrator that ingests contracts, extracts clauses, flags risk, routes high-risk cases to human reviewers, and tracks measurable business value (agent-hours unlocked, risk coverage, and throughput).

## Current MVP Truth

The implemented MVP currently focuses on:

- LangGraph Studio execution
- local file-path intake
- `TXT`, `MD`, `DOCX`, and selectable-text `PDF` parsing
- provider-backed extraction for `openai`, `gemini`, and `grok`
- heuristic fallback when provider calls fail and fallback is enabled
- deterministic policy routing
- Studio-based human review interrupt
- local audit and reporting

The docs may still discuss broader future capabilities such as redlines, retrieval grounding, or business-system integrations. Those should be treated as next-step roadmap items unless the code explicitly supports them.
