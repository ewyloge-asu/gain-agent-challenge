---
id: T-0002
title: "Senate vs House disclosure discrepancies"
status: cold
priority: 5
workflow_step: "xref.py mismatch --year 2025"
entities: []
findings: []
source_records:
  - "mapper xref mismatch scan, 2025 Senate+House filings"
next_action: ""
reason: "Checked — the two systems reconcile well; largest 2025 income gap for the same engagement is ~$90k. Not a story."
---

## Hypothesis
Same engagement filed differently in Senate vs House would signal disclosure gaming.

## Why cold
Ran the mismatch scan at $250k, $50k thresholds. Only two trivial gaps surfaced (max ~$90k). The
datasets reconcile. Revivable only if a specific large discrepancy is found later.
