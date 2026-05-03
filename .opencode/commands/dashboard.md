---
description: Regenerate the static task dashboard and open it in the browser
---

Run `bash scripts/open_dashboard.sh` from the repository root. Do not run any other commands.

```bash
bash scripts/open_dashboard.sh
```

## Output rules

- If the command succeeds (exit code 0): print one short confirmation line and the output file path. Nothing else.
- If the command fails (non-zero exit): print the exit code and the stderr output. Then stop — do not print the task board summary in chat.

## Scope

- Do not read or summarise task files.
- Do not print the task board in chat.
- Do not start a server or background process.
- Do not modify any file other than `dashboards/task-dashboard.html`.
