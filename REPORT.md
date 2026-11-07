# Workflow vs plain skills on Hermes: pilot results

Generated 2026-11-06 from raw result files in `results/`. Pilot only: small suite, one model, few runs. Treat numbers as a first look, not proof.

## Comparison

| Measure | Plain skill (baseline) | Workflow (helper agents + code checks) |
|---|---|---|
| Scored runs | 30 | 10 |
| Strict success (exact output contract) | 28/30 | 9/10 |
| Semantic success (right invoices, reasons, drafts) | 28/30 | 9/10 |
| System ended in the right state | 29/30 | 9/10 |
| Tasks passed in every run (pass^k) | 8/10 | 9/10 |
| Invented ids or codes | 13/1010 | 0/187 |
| Reason-text format slips | 0 | 0 |
| Mean step adherence | 0.99 | 0.90 |
| Mean cost per task, all-in (USD) | 0.0105 | 0.0482 |
| Mean API calls per task, all-in | 10.9 | 52.9 |
| Median seconds per task | 24.6 | 42.0 |

All-in cost and calls include helper agents (read from exported sessions), because Hermes' own usage report covers only the parent agent.

## Per task (passes / runs)

| Task | Baseline | Workflow |
|---|---|---|
| T01 | 3/3 | 1/1 |
| T02 | 3/3 | 1/1 |
| T03 | 2/3 | 1/1 |
| T04 | 3/3 | 1/1 |
| T05 | 3/3 | 1/1 |
| T06 | 3/3 | 1/1 |
| T07 | 3/3 | 1/1 |
| T08 | 3/3 | 1/1 |
| T09 | 2/3 | 1/1 |
| T10 | 3/3 | 0/1 |

**In one line:** on this suite the workflow scored 9/10 strict versus 28/30 for the baseline, at 4.6x the cost and 4.9x the API calls per task.

## Findings from reading the transcripts

1. **Baseline false rejection (T03).** On the task with one missing purchase order, the plain skill sometimes rejected a clean invoice (T03-INV-04) as `quantity_exceeds_delivery`. In the exported session the agent sent all lookups in parallel, received a "no deliveries found" error that does not name its purchase order, and attached it to the wrong invoice. The data was correct.
2. **Baseline arithmetic and format slips (T09).** In one 30-invoice run the agent got every classification right but appended explanations to every reason, breaking the output contract, and its shown sums were wrong (for example it wrote lines 1,177.50 where the true subtotal was 652.50). The classification was right; the visible arithmetic was not.
3. **Hermes already treats tool output as untrusted data,** which probably explains why the injection traps passed on the baseline.
4. **Workflow design constraint.** Hermes one-shot mode caps helper agents at 2 per run by default (`delegation.oneshot_max_children`), and 10 in parallel per call. Without raising the cap, the helpers are refused and the agent falls back to doing the work itself.

## Caveats (please read)

- One model only (Claude Haiku 5.5 through OpenRouter, reasoning medium). Results may differ on weaker or stronger models.
- Suite v0.1 (8 tasks) was passed fully by the baseline, so two larger tasks (30 and 60 invoices) were added afterwards as suite v0.2. T01 to T08 were not changed.
- Early runs on free models were discarded (rate limits, retired models). A stale tool server wrongly broke T09 and T10 once; those runs were deleted and redone.
- The workflow runs needed `delegation.oneshot_max_children` raised to 0 (unlimited) in the Hermes config. Baseline runs do not use helpers.
- Tool error replies do not name the item they refer to. Naming it would probably help the baseline.
- Strict success requires the exact output contract (reason = a bare code). Semantic success ignores extra words.
- Number of runs per condition is small; see the table.

## Recommendation (edit after reading the numbers)

[Write 2 to 3 sentences: did the workflow beat the baseline on reliability, and was it worth the extra cost? Which option (A subagents, B external runner, C context engine) would you build next, and what is the smallest first version worth shipping?]
