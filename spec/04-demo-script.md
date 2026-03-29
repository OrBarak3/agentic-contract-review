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

"A global procurement team is overloaded with contract reviews and misses SLA targets. We will show how this workflow accelerates low-risk work while improving risk coverage and auditability."

## Live Flow

1. Intake (3 minutes)
   - Upload two contracts:
     - Contract A: standard, low-risk.
     - Contract B: non-standard liability language, high-risk.
   - Show metadata and processing kickoff.
2. Agent Extraction (4 minutes)
   - Show structured clause extraction and evidence spans.
   - Show confidence scores and model output schema.
3. Policy + Routing (4 minutes)
   - Contract A routes to auto-path due to policy pass.
   - Contract B routes to human review due to high-risk clause.
4. Human Review (5 minutes)
   - Reviewer edits risk tag/redline for Contract B.
   - Reviewer approves final action.
5. Integrations + Audit (4 minutes)
   - CRM status update.
   - Ticket creation/closure.
   - Decision trace log (model, prompt, policy, actor, timestamp).
6. KPI Snapshot (3 minutes)
   - Baseline vs pilot metrics dashboard.
   - Discuss rollout readiness criteria.

## Screens or Artifacts to Prepare

- Processing timeline view per contract.
- Clause extraction JSON (cleanly formatted).
- Reviewer queue with side-by-side original vs proposed redline.
- Audit trail table.
- KPI scorecard.

## Q&A Prompts You Should Be Ready For

- "How do you prevent hallucinated clauses from triggering actions?"
- "What changed when confidence was wrong but high?"
- "How quickly can this adapt to a new customer policy?"
- "What does rollback look like if a model update regresses quality?"

## Strong Closing

"This project is intentionally built as a deployable customer workflow: measurable outcomes, clear governance controls, reusable integration patterns, and a practical path from pilot to scaled rollout."
