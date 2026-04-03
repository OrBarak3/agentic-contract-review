---
name: policy
description: Explain the governance model, policy routing logic, and YAML policy pack structure.
---

Read and explain the following:

1. `policies/default_policy.yaml` — the active policy pack (confidence thresholds, blocked clause types, routing rules)
2. `contract_review_langgraph/policies.py` — how policy packs are loaded and how routing decisions are made deterministically
3. `contract_review_langgraph/graph.py` — the conditional edges that route between `auto_advance`, `human_review`, and `rejected` based on policy outcomes

When explaining:
- Describe the **governance invariant**: AI proposes (LLM extracts clause risk/type/confidence), policy decides (YAML + Python rules evaluate extractions), human approves (interrupt node for borderline/high-risk cases).
- Identify which fields in the policy YAML control routing (confidence thresholds, blocked clause types, risk level rules).
- Explain why routing logic lives in Python/YAML rather than in prompts — to keep it auditable, deterministic, and version-controllable.
- Show the decision path for a clause that triggers human review vs. one that auto-advances.
