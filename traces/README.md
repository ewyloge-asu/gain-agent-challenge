# Interaction traces

This folder keys each finding to the exact skill invocations that produced it,
so an evaluator can re-run a single command and reproduce a single number rather
than re-reading the whole session.

- [invocation_log.md](invocation_log.md) — finding → commands → key outputs.

The full model session (the agent's reasoning, tool calls, and the human
judgment points where the investigation was steered) is the chat transcript that
accompanies this submission. The mapping below is the machine-checkable spine of
that session: every headline number traces to one command here, and every command
traces to source records via `scripts/review.py`.

## Re-run everything
```bash
export GAIN_DATA_DIR=/path/to/data
bash ../lobbying-influence-mapper/scripts/run_all.sh
```
