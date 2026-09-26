# Contributing

Start with the [working agreement](docs/working-agreement.md). It is short, and it explains why the rules below exist.

## Setup

Run every command from the repository root.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Put API keys in a local `.env` file. It is gitignored; never commit it.

CI checks for personal data and local paths only after a push, when the content is already public. Install a local pre-push hook, so that the same check runs before anything leaves your machine and a failure stops the push:

```bash
printf '#!/bin/sh\nexec python3 scripts/check_public.py\n' > .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

## Where things are

| Path | What it holds | Guide |
|---|---|---|
| `src/tracemem/schema.py`, `components.py`, `ops.py`, `systems/base.py` | the contracts: data types, component interfaces, what each memory operation does, and the interface every compared system offers the harness | [interfaces](docs/interfaces.md) |
| `benchmark/scenarios/dev/` | development scenarios: scripts and dialogue | [benchmark](docs/benchmark.md) |
| `src/tracemem/eval/` | the harness and the scorer | [metrics](docs/metrics.md) |
| `docs/decisions/` | decision records | [how to write one](docs/decisions/README.md) |

## Pull requests

- Branch from `main`, keep the change small, and ask the teammate who consumes your output to review it.
- CI must pass: tests, the scenario validator, the decision-record checker, and the public-content check.
- A change to a contract file (`schema.py`, `components.py`, `ops.py`, `systems/base.py`) is a contract change: label it `contract-change` and get approval from every consuming owner.
- If your change embodies a decision that affects others, add a decision record.
