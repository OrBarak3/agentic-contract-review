# 04 - Demo Script

## Demo Objective

Show a believable end-to-end enterprise workflow that combines AI agents, policy governance, and human oversight to deliver measurable value.

## Audience

- Technical recruiter
- Hiring manager (Solutions Engineering / Sales Engineering)
- Cross-functional panel (product + GTM)

## Demo Length

20 to 25 minutes

## Storyline

"A mid-market SaaS company is reviewing a growing volume of vendor MSAs and procurement agreements. We will show how a LangGraph Studio workflow accelerates standard contracts, escalates risky language to a reviewer, and leaves behind a clear audit trail."

## Live Flow

1. Intake (3 minutes)
   - Run two local fixture contracts by filesystem path in LangGraph Studio:
     - Contract A: standard, low-risk.
     - Contract B: non-standard liability language, high-risk.
   - Show run metadata and graph kickoff.
2. Agent Extraction (4 minutes)
   - Show structured clause extraction and evidence spans.
   - Show confidence scores and normalized output schema.
3. Policy + Routing (4 minutes)
   - Contract A routes to auto-path due to policy pass.
   - Contract B routes to human review due to high-risk clause.
4. Human Review (5 minutes)
   - Reviewer uses the LangGraph interrupt to edit risk tags or approve/reject Contract B.
   - Reviewer approves final action.
5. Audit + Reporting (4 minutes)
   - Node-level event history with provider/model metadata, policy reasons, and reviewer action.
   - SQLite / JSONL / Markdown run artifacts.
6. KPI Snapshot (3 minutes)
   - Baseline vs pilot metrics dashboard.
   - Call out agent-hours of reviewer capacity unlocked as the headline business outcome.
   - Discuss rollout readiness criteria and what would be added next.

## Example Inputs

Use the repo fixtures with absolute paths in Studio:

```json
{
  "contract_path": "/absolute/path/to/agentic-contract-review/fixtures/low_risk_vendor_msa.txt",
  "provider": "openai",
  "policy_pack": "/absolute/path/to/agentic-contract-review/policies/default_policy.yaml",
  "run_label": "demo-low-risk"
}
```

```json
{
  "contract_path": "/absolute/path/to/agentic-contract-review/fixtures/high_risk_vendor_msa.txt",
  "provider": "openai",
  "policy_pack": "/absolute/path/to/agentic-contract-review/policies/default_policy.yaml",
  "run_label": "demo-high-risk"
}
```

When the high-risk contract pauses in `human_review`, resume with a payload like:

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

## Screens or Artifacts to Prepare

- LangGraph Studio graph view.
- Processing timeline view per contract.
- Clause extraction JSON (cleanly formatted).
- Human review interrupt payload and resume action.
- Audit trail table.
- KPI scorecard.
- One generated Markdown report from `runtime/reports/`.

## Q&A Prompts You Should Be Ready For

- "How do you prevent hallucinated clauses from triggering actions?"
- "What changed when confidence was wrong but high?"
- "How quickly can this adapt to a new customer policy?"
- "What does rollback look like if a model update regresses quality?"
- "Why LangGraph Studio first instead of a customer-facing app?"
- "How do you keep the demo running if an API key is missing or a provider call fails?"

## Strong Closing

"This project is intentionally built as a deployable customer workflow: measurable outcomes, clear governance controls, a working LangGraph Studio execution path, and a practical roadmap from demo-quality orchestration to customer-ready deployment."
