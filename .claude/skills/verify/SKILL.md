---
name: verify
description: Run the test suite and report results. Invoke before marking any task complete.
---

Run the following command and report the full output:

```bash
pytest tests/ -v
```

If tests fail, identify which test failed and why, then fix the root cause before reporting done. Do not mark a task complete while any tests are failing.
