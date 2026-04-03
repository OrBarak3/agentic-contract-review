---
name: demo
description: Invoke the contract review graph end-to-end on a fixture contract and display audit output.
disable-model-invocation: true
---

Run the contract review workflow on the low-risk fixture contract and show the results.

```bash
python -c "
import asyncio
from langgraph.checkpoint.memory import MemorySaver
from contract_review_langgraph.graph import graph
from contract_review_langgraph.config import AppPaths

checkpointer = MemorySaver()
config = {'configurable': {'thread_id': 'demo-run'}}

initial_state = {
    'contract_path': 'fixtures/low_risk_vendor_msa.txt',
    'run_id': 'demo-run',
}

async def run():
    async for event in graph.astream(initial_state, config=config):
        print(event)

asyncio.run(run())
"
```

After the graph runs, show the contents of the latest report:

```bash
ls -t runtime/reports/*.md 2>/dev/null | head -1 | xargs cat
```

If Studio is running (`langgraph dev`), you can also open the Studio UI instead and run the workflow interactively with thread ID `demo-run`.

To test the high-risk path, replace `low_risk_vendor_msa.txt` with `high_risk_vendor_msa.txt` — this will route to the `human_review` interrupt node.
