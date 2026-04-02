# Review: Agentic Contract Review Orchestrator vs. Wand SE Role

**Overall: 8/10.** Genuinely strong. The spec pack structure itself signals CE methodology, and the Proof-to-Contract eval doc shows you read the JD carefully — Wand uses that exact term as a core role responsibility. Here's the full breakdown:

---

## What lands well

- **Direct JD mirror** — The JD literally names "contract review" as a sample CE pattern. You picked the right use case.
- **Proof-to-Contract eval framework (doc 03)** — Wand explicitly lists "Lead technical validation (Proof-to-Contract)" as a key responsibility. Having a full eval spec for this is a strong signal.
- **Governance model** — "AI proposes, policy decides, human approves" maps directly to Wand's pitch of safe, transparent hybrid workforces.
- **Reusable CE patterns** — Charter calls out "reusable templates/policy packs," exactly what the JD asks for.
- **Measurable outcomes with baselines** — Concrete KPIs with baseline vs. pilot design, not just vibes.

---

## Gaps and suggestions

### 1. Repo name mismatch
~~`agentic-emails` vs. a contract review project.~~ **Fixed** — repo renamed to `agentic-contract-review` and README fully rewritten.

### 2. No Wand vocabulary
~~Wand sells "agent-hours" as a unit of value. Your metrics use standard SLA language (cycle time, throughput). Reframe at least one metric as *agent-hours of capacity unlocked* — it shows you've internalized their product model, not just the generic SE playbook.~~ **Fixed** — added `agent-hours of review capacity unlocked` as a named KPI, defined what it means, and carried it through the README, charter, system design, eval spec, and demo narrative.

### 3. Single-agent design undersells the "agentic" framing
Wand's identity is agentic labor infrastructure with multi-agent orchestration. Your current architecture has one LLM extraction agent. Consider breaking it into coordinator → specialized sub-agents (extractor, risk classifier, redline generator) to show you think in agent graphs, not just LLM calls.

### 4. No RAG component
The JD explicitly calls out RAG as an expected skill. Your policy engine is deterministic rules, but grounding the risk classifier against a *retrieved policy knowledge base* (past contracts, policy templates) would demonstrate RAG and make the system more realistic.

### 5. Tech stack is too vague
~~"Python-first" and "LLM extraction" isn't enough. The JD wants to see practical experience. Add specifics to `02-system-design.md`: Pydantic for schema validation, FastAPI for the reviewer API, Claude/OpenAI for LLM calls (with which model and why), LangChain or raw API calls (and the tradeoff).~~ **Fixed** — added a full `## Tech Stack` section to `02-system-design.md` with: FastAPI (with rationale vs Flask/Django), Pydantic v2 for all data models, Claude Opus 4.6 as primary + Haiku 4.5 as fallback (with model rationale), raw Anthropic SDK with an explicit LangChain tradeoff, pdfplumber/pytesseract/python-docx for parsing, PostgreSQL + Redis for storage, pgvector + embeddings for the RAG/policy KB, and pytest + pytest-asyncio for testing.

### 6. Demo storyline is generic
"Global procurement team overloaded" could be any product pitch. Pick a vertical: e.g., *a mid-market SaaS company reviewing 80+ vendor MSAs/month ahead of a Series B audit*. Specificity makes the story memorable and shows customer empathy.

### 7. Missing: "how you'd hand this off"
The JD emphasizes turning one deployment into a pattern others can reuse. Add a short section to doc 05 — even a stub — called "CE Handoff Kit": what you'd document, what policy config is customer-specific vs. reusable, and what onboarding looks like for the next SE or customer. This is exactly the "systems thinker" quality Wand is screening for.

### 8. 14-day scope is risky
OCR pipeline + extraction + policy engine + reviewer UI + 2 integrations + eval harness + hardening in 14 days solo is very aggressive. If you don't ship it fully, the spec pack alone won't close the interview. Consider either narrowing the scope (stub 1 integration, use a simple CLI for the reviewer interface) or explicitly noting in the roadmap which pieces are "demo-quality" vs. "production-quality" — that framing itself shows SE maturity.

---

## Priority changes to make

| Priority | Change |
|---|---|
| High | Rename repo or fix README mismatch |
| High | Add Wand-specific "agent-hours" framing to metrics |
| High | Add RAG layer to system design |
| Medium | Expand to multi-agent architecture diagram |
| ~~Medium~~ | ~~Add concrete tech stack to doc 02~~ ✓ Done |
| Medium | Add "CE Handoff Kit" stub to doc 05 |
| Low | Sharpen the demo storyline to a specific vertical |

The foundation is solid — most of these are additions or reframings, not rebuilds.

---

## Implementation Readiness Check

**Status: mostly ready, but 3 gaps would cause mid-build rework.**

### What's solid enough to start now
- Data models, routing rules, repo structure — enough to start Day 1-3 tasks (ingestion, parsing, schemas).
- Tech stack decisions are now concrete (doc 02).
- Eval harness design (doc 03) is detailed enough to implement against.

### Gaps that block the agent/policy layer

| Gap | Why it matters | Priority |
|---|---|---|
| **Multi-agent graph not designed** (point 3) | Spec still shows one `LLM Extraction Agent`. Building without the coordinator → extractor → risk classifier → redline generator graph means reworking the agent layer mid-build. | Medium |
| **RAG retrieval flow not designed** (point 4) | Tech stack now mentions pgvector, but doc 02 doesn't show *when* retrieval happens, *what* gets retrieved, or how it connects to the policy engine. | High |
| **Demo vertical not picked** (point 6) | Doesn't block code, but the vertical choice (e.g. SaaS MSAs) determines the fixture contracts for the eval harness. | Low |

### Low-effort remaining
- CE Handoff Kit stub in doc 05 (a few paragraphs).
- Label roadmap tasks as "demo-quality" vs "production-quality" to address scope risk (point 8).

**Recommended order:** Design RAG flow + multi-agent graph in doc 02 first (~1 hour), then start implementation. Days 1-2 foundation work can begin in parallel since ingestion/parsing/schema are fully spec'd.
