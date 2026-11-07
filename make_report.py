"""Builds REPORT.md (comparison table, per-task results, findings, caveats) from the results files.
  python3 make_report.py            # uses results/baseline.jsonl and results/workflow.jsonl"""
import json, statistics as st, pathlib, datetime
R = pathlib.Path(__file__).parent / "results"

def load(name):
    p = R / f"{name}.jsonl"
    rows = [json.loads(l) for l in open(p)] if p.exists() else []
    return [r for r in rows if not r.get("infra_failed")], len(rows)

def allin(r):
    u = r.get("usage") or {}
    t = u.get("total_including_auxiliary") or {}
    h = ((u.get("helpers") or {}).get("totals")) or {}
    return (t.get("estimated_cost_usd") or 0) + h.get("cost_usd", 0), (t.get("api_calls") or 0) + h.get("api_calls", 0)

def summarize(rows):
    if not rows:
        return None
    n = len(rows); by = {}
    for r in rows: by.setdefault(r["task_id"], []).append(r)
    costs = [allin(r)[0] for r in rows]; calls = [allin(r)[1] for r in rows]
    return {"runs": n, "tasks": len(by),
            "strict": sum(r["success"] for r in rows), "semantic": sum(r.get("semantic_correct", r["success"]) for r in rows),
            "outcome": sum(r.get("outcome_correct", r["success"]) for r in rows),
            "pass_all": sum(all(x["success"] for x in v) for v in by.values()),
            "ungrounded": sum(r["fields_ungrounded"] for r in rows), "fields": sum(r["fields_total"] for r in rows),
            "slips": sum(r.get("reason_format_slips", 0) for r in rows),
            "adherence": st.mean(r["adherence"] for r in rows), "seconds": st.median(r["seconds"] for r in rows),
            "cost": st.mean(costs), "calls": st.mean(calls), "by": by,
            "parent_tokens": st.mean(((r.get("usage") or {}).get("total_including_auxiliary") or {}).get("total_tokens") or 0 for r in rows)}

b_rows, b_all = load("baseline"); w_rows, w_all = load("workflow")
B, W = summarize(b_rows), summarize(w_rows)
def f(S, k, fmt="{}"):
    return fmt.format(S[k]) if S else "not run"
L = []
L.append(f"# Workflow vs plain skills on Hermes: pilot results\n\nGenerated {datetime.date.today()} from raw result files in `results/`. Pilot only: small suite, one model, few runs. Treat numbers as a first look, not proof.\n")
L.append("## Comparison\n\n| Measure | Plain skill (baseline) | Workflow (helper agents + code checks) |\n|---|---|---|")
rows_t = [("Scored runs", f(B, "runs"), f(W, "runs")),
 ("Strict success (exact output contract)", f"{B['strict']}/{B['runs']}" if B else "n/a", f"{W['strict']}/{W['runs']}" if W else "not run"),
 ("Semantic success (right invoices, reasons, drafts)", f"{B['semantic']}/{B['runs']}" if B else "n/a", f"{W['semantic']}/{W['runs']}" if W else "not run"),
 ("System ended in the right state", f"{B['outcome']}/{B['runs']}" if B else "n/a", f"{W['outcome']}/{W['runs']}" if W else "not run"),
 ("Tasks passed in every run (pass^k)", f"{B['pass_all']}/{B['tasks']}" if B else "n/a", f"{W['pass_all']}/{W['tasks']}" if W else "not run"),
 ("Invented ids or codes", f"{B['ungrounded']}/{B['fields']}" if B else "n/a", f"{W['ungrounded']}/{W['fields']}" if W else "not run"),
 ("Reason-text format slips", f(B, "slips"), f(W, "slips")),
 ("Mean step adherence", f"{B['adherence']:.2f}" if B else "n/a", f"{W['adherence']:.2f}" if W else "not run"),
 ("Mean cost per task, all-in (USD)", f"{B['cost']:.4f}" if B else "n/a", f"{W['cost']:.4f}" if W else "not run"),
 ("Mean API calls per task, all-in", f"{B['calls']:.1f}" if B else "n/a", f"{W['calls']:.1f}" if W else "not run"),
 ("Median seconds per task", f"{B['seconds']:.1f}" if B else "n/a", f"{W['seconds']:.1f}" if W else "not run")]
for r in rows_t: L.append("| " + " | ".join(r) + " |")
L.append("\nAll-in cost and calls include helper agents (read from exported sessions), because Hermes' own usage report covers only the parent agent.\n")
L.append("## Per task (passes / runs)\n\n| Task | Baseline | Workflow |\n|---|---|---|")
for t in sorted({r["task_id"] for r in b_rows + w_rows}):
    g = lambda S: f"{sum(x['success'] for x in S['by'][t])}/{len(S['by'][t])}" if S and t in S["by"] else "-"
    L.append(f"| {t} | {g(B)} | {g(W)} |")
if B and W and B["cost"] > 0:
    L.append(f"\n**In one line:** on this suite the workflow scored {W['strict']}/{W['runs']} strict versus {B['strict']}/{B['runs']} for the baseline, at {W['cost']/B['cost']:.1f}x the cost and {W['calls']/B['calls']:.1f}x the API calls per task.\n")
L.append("""## Findings from reading the transcripts

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
""")
(pathlib.Path(__file__).parent / "REPORT.md").write_text("\n".join(L))
print("wrote REPORT.md"); print("\n".join(L[:30]))
