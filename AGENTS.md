# Instructions for AI coding assistants

These rules apply to any AI assistant that reads or edits this repository. They repeat the parts of [`docs/working-agreement.md`](docs/working-agreement.md) that matter most for automated edits; the working agreement wins where the two differ.

## Setup and checks

```bash
pip install -e ".[dev]"
pytest                                   # includes the scorer self-tests
tracemem validate                        # development scenarios must validate
python scripts/check_decisions.py        # decision records must agree
python scripts/check_public.py           # no personal data or local paths
```

Run all four before proposing a change, and report their output honestly, including failures.

## Hard rules

1. **Do not open, read, summarise or tune on test scenarios.** They are held outside this repository until the freeze; if any appear under `benchmark/scenarios/test/`, leave them alone. If a task seems to require them, stop and ask the human.
2. **Do not change prompts or settings after a `freeze-*` tag** without a decision record that says so.
3. **Do not change the contract files silently:** `src/tracemem/schema.py`, `src/tracemem/components.py`, `src/tracemem/ops.py` and `src/tracemem/systems/base.py`. A contract change needs a pull request labelled `contract-change`, updated fixtures and tests in the same change, and approval from every owner who consumes the changed type.
4. **Do not hand-write a scenario's expected answers.** The benchmark's gold is computed by `tracemem replay` from each script. (Tests are the exception: `tests/test_replay.py` holds hand-derived tables precisely so that a bug in the replay is caught.)
5. **Do not weaken a test to make it pass.** The scorer self-tests in `tests/test_metrics.py` exist to fail on a broken scorer; a change that makes them pass by loosening them is a bug.
6. **Never commit secrets or personal data.** API keys belong in a local `.env`. Student IDs, e-mail addresses and phone numbers never appear in code, data, logs or commit messages.
7. **Do not push to `main`.** Work on a branch; a human opens and owns the pull request.

## Conventions

- Keep changes small and within one component unless the task says otherwise.
- Every identifier carries its gloss: write "S2-T3 ('Maybe we could try DistilBERT?')", not a bare "S2-T3".
- Scenarios are synthetic. Do not copy real conversations or names into them.
- A decision that affects more than one person gets a record in `docs/decisions/`.
