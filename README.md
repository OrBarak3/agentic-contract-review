# agentic-emails
routes customer support emails to an LLM automatic answering for low-medium risk cases and to human review for high risk cases

[INBOUND EMAIL]
      |
      v
[INGESTION LAYER]
- receive email (API / SMTP)
- attach metadata (user_id, timestamp)
- enqueue (Kafka / SQS)
      |
      v
[PREPROCESSING]
- clean text (remove signatures, threads)
- extract attachments (OCR if needed)
- normalize format
      |
      v
[LLM: CLASSIFY + EXTRACT (STRUCTURED)]
- input: email + context
- output (JSON):
    issue_type
    entities (order_id, product, etc.)
    intent
    confidence
    draft_response
      |
      v
[VALIDATION LAYER]
- schema validation (types, required fields)
- business rules:
    valid order_id?
    known issue_type?
    policy constraints?
      |
      +----------------------+
      |                      |
      v                      v
[FAIL]                  [PASS]
- retry (prompt fix)     |
- fallback model         |
- or human               v
                   [CONFIDENCE GATE]
                   - confidence >= threshold?
                         |
               +---------+---------+
               |                   |
               v                   v
        [LOW CONF / HIGH RISK]   [HIGH CONF / LOW RISK]
               |                   |
               v                   v
     [HUMAN-IN-THE-LOOP]     [AUTO RESOLUTION]
     - show extracted data   - trigger APIs (refund, reset, etc.)
     - show draft response   - finalize response
     - human edits           |
               |             v
               +------> [RESPONSE GENERATION]
                          - render email from structured data
                          - apply templates/tone
                          |
                          v
                     [SEND EMAIL]
                          |
                          v
                     [STORAGE]
                     - raw email
                     - structured output
                     - final action
                     - human edits (if any)
                          |
                          v
                [EVALUATION & MONITORING]
                - accuracy (per field)
                - automation rate
                - escalation rate
                - latency
                          |
                          v
                [CONTINUOUS IMPROVEMENT]
                - error analysis
                - update prompts / rules
                - re-run evals