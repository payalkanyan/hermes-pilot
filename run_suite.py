"""Runs every task N times for one condition (baseline or workflow), grades, and prints a table.
  python run_suite.py --condition baseline --runs 3 --oracle        # self-test with a perfect fake agent
  AGENT_CMD='hermes ... {prompt}' python run_suite.py --condition baseline --runs 3
AGENT_CMD is a shell command. {prompt} is replaced by the quoted prompt and {usage} by a per-run file path;
its stdout is taken as the agent's final answer, and if it writes JSON to {usage} that is saved with the run."""
import argparse, json, os, shlex, statistics, subprocess, time, pathlib
import world_api as W
import helper_usage
from grade import grade, load_calls
ROOT = pathlib.Path(__file__).parent

def oracle(task):
    out = {"matched": [], "exceptions": []}
    for iid, why in task["expected"]["exceptions"].items():
        W.get_invoice(iid); out["exceptions"].append({"invoice_id": iid, "reason": why})
    for iid in task["expected"]["matched"]:
        inv = W.get_invoice(iid); po = inv["po_ref"]; W.get_purchase_order(po); W.get_deliveries(po)
        d = W.create_draft_bill(iid, po, inv["total"]); W.get_draft_bill(d["draft_id"])
        out["matched"].append({"invoice_id": iid, "po_id": po, "draft_id": d["draft_id"]})
    return "Done.\n" + json.dumps(out)

def real_agent(task, condition, run):
    prompt = (f"Use the invoice-matching-{condition} skill to process mailbox folder {task['folder']} "
              f"for {task['month']}. The folder is in the invoice tools, not a folder on disk.")
    usage = ROOT / "results" / f"usage-{condition}{'-' + a.tag if a.tag else ''}-{task['task_id']}-r{run}.json"
    usage.unlink(missing_ok=True)
    cmd = os.environ["AGENT_CMD"].replace("{prompt}", shlex.quote(prompt)).replace("{usage}", shlex.quote(str(usage)))
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1800)
    u = None
    if usage.exists():
        try: u = json.loads(usage.read_text())
        except Exception: u = None
    helpers = None
    if condition == "workflow" and isinstance(u, dict) and u.get("session_id"):
        d = ROOT / "results" / "sessions"
        d.mkdir(exist_ok=True)
        try:
            subprocess.run(["hermes", "sessions", "export", "--format", "md", "--redact", "--session-id", u["session_id"][:24], str(d) + "/"],
                           capture_output=True, text=True, timeout=120)
            files = sorted(d.glob(u["session_id"][:24] + "*.md"))
            if files:
                helpers = helper_usage.parse_md(files[-1])
        except Exception:
            helpers = None
    if isinstance(u, dict):
        u["helpers"] = helpers
    return out.stdout, u

ap = argparse.ArgumentParser()
ap.add_argument("--condition", required=True, choices=["baseline", "workflow"])
ap.add_argument("--runs", type=int, default=3)
ap.add_argument("--oracle", action="store_true")
ap.add_argument("--max-cost", type=float, default=None, help="stop once reported cost (USD) exceeds this")
ap.add_argument("--tasks", default=None, help="comma list, e.g. T01,T03")
ap.add_argument("--tag", default="", help="write to a separate results file, e.g. diag")
ap.add_argument("--resume", action="store_true", help="keep finished runs, redo runs Hermes reported as failed")
a = ap.parse_args()
tasks = [json.loads(l) for l in open(ROOT / "data" / "tasks.jsonl")]
if a.tasks:
    tasks = [t for t in tasks if t["task_id"] in a.tasks.split(",")]
res_path = ROOT / "results" / f"{a.condition}{'-' + a.tag if a.tag else ''}{'-oracle' if a.oracle else ''}.jsonl"
def infra(g):  # Hermes itself said the run failed (rate limit, provider error): not the agent's fault
    u = g.get("usage")
    return isinstance(u, dict) and bool(u.get("failed") or u.get("completed") is False)
kept = []
if a.resume and res_path.exists():
    kept = [g for g in map(json.loads, open(res_path)) if not infra(g)]
res_path.write_text("".join(json.dumps(g) + "\n" for g in kept))
done = {(g["task_id"], g["run"]) for g in kept}
stopped = None
spent = 0.0
for t in tasks:
    for r in range(a.runs):
        if (t["task_id"], r + 1) in done or stopped:
            continue
        W.reset(); t0 = time.time()
        text, usage = (oracle(t), None) if a.oracle else real_agent(t, a.condition, r + 1)
        g = grade(t, text, W._state(), load_calls(W.LOG), W.WORLD)
        g.update(run=r + 1, seconds=round(time.time() - t0, 1), usage=usage, raw_answer=text)
        g["infra_failed"] = infra(g)
        broken = [c for c in load_calls(W.LOG) if c["tool"] == "list_invoices" and c["args"].get("folder") == t["folder"]
                  and isinstance(c["result"], dict) and "error" in c["result"]]
        if broken:  # the agent's tool server does not know this folder: a setup fault, not an agent mistake
            g["infra_failed"] = True
            g["setup_error"] = "tool server returned folder-not-found (stale server? restart it and re-run)"
            stopped = stopped or f"Stopped at {t['task_id']}: the agent's tool server does not know folder {t['folder']}. Run: pkill -f mock_server.py  then re-run with --resume."
        open(res_path, "a").write(json.dumps(g) + "\n")
        c = ((usage or {}).get("total_including_auxiliary") or {}).get("estimated_cost_usd")
        spent += c if isinstance(c, (int, float)) else 0
        hc = (((usage or {}).get("helpers") or {}).get("totals") or {}).get("cost_usd")
        spent += hc if isinstance(hc, (int, float)) else 0   # helper agents' cost counts toward the limit too
        if a.max_cost is not None and spent >= a.max_cost and not stopped:
            stopped = f"Stopped: reported spend ${spent:.2f} reached --max-cost {a.max_cost}. Continue with --resume."
        if g["infra_failed"] and "429" in str((usage or {}).get("failure", "")):
            stopped = f"Stopped at {t['task_id']} run {r + 1}: provider rate limit (HTTP 429). Re-run the same command with --resume later."
allrows = [json.loads(l) for l in open(res_path)]
rows = [x for x in allrows if not x.get('infra_failed')]
def flat(d, pre=""):
    out = {}
    for k, v in (d or {}).items():
        if isinstance(v, dict):
            if k not in ("by_task", "helpers"): out.update(flat(v, f"{pre}{k}."))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[f"{pre}{k}"] = v
    return out
print(f"{'task':5} {'pass':5} pass^{a.runs}")
for t in tasks:
    rr = [x for x in rows if x["task_id"] == t["task_id"]]
    if not rr:
        print(f"{t['task_id']:5} --    not run (provider failure or stopped)"); continue
    print(f"{t['task_id']:5} {sum(x['success'] for x in rr)}/{len(rr)}   {'yes' if len(rr) == a.runs and all(x['success'] for x in rr) else 'no'}")
n = len(rows); ft = sum(x["fields_total"] for x in rows)
print(f"\nscored runs {len(rows)} of {len(allrows)} (provider-failed runs are excluded, not counted as wrong)")
print(f"task success      {sum(x['success'] for x in rows)}/{n}")
print(f"outcome correct   {sum(x['outcome_correct'] for x in rows)}/{n}   (the fake accounting system ended in the right state)")
print(f"semantic correct  {sum(x.get('semantic_correct', x['success']) for x in rows)}/{n}   (right invoices, right reasons by code, right drafts; ignores extra words in the reason text)")
print(f"reason text slips {sum(x.get('reason_format_slips', 0) for x in rows)} exception(s) had the right reason code plus extra words")
print(f"report correct    {sum(x['report_correct'] for x in rows)}/{n}   (the final JSON answer is valid and right)")
print(f"hallucination     {sum(x['fields_ungrounded'] for x in rows)}/{ft} fields")
print(f"step adherence    {statistics.mean([x['adherence'] for x in rows] or [0]):.2f}")
print(f"median seconds    {statistics.median([x['seconds'] for x in rows] or [0])}")
seen = sorted({f"{x['usage'].get('provider')} / {x['usage'].get('model')}" for x in allrows if isinstance(x.get("usage"), dict)})
if seen:
    print("model used        " + "; ".join(seen) + ("   <-- MORE THAN ONE MODEL, do not compare these runs" if len(seen) > 1 else ""))
hl = [x["usage"]["helpers"] for x in rows if isinstance(x.get("usage"), dict) and isinstance(x["usage"].get("helpers"), dict)]
if hl:
    pc = [((x["usage"].get("total_including_auxiliary") or {}).get("estimated_cost_usd") or 0) for x in rows if isinstance(x.get("usage"), dict) and isinstance(x["usage"].get("helpers"), dict)]
    pa = [((x["usage"].get("total_including_auxiliary") or {}).get("api_calls") or 0) for x in rows if isinstance(x.get("usage"), dict) and isinstance(x["usage"].get("helpers"), dict)]
    hc = [h["totals"].get("cost_usd", 0) for h in hl]; ha = [h["totals"].get("api_calls", 0) for h in hl]
    print(f"ALL-IN (parent + helpers) mean cost per task  ${statistics.mean(p + c for p, c in zip(pc, hc)):.4f}   (parent ${statistics.mean(pc):.4f} + helpers ${statistics.mean(hc):.4f})")
    print(f"ALL-IN (parent + helpers) mean API calls      {statistics.mean(p + c for p, c in zip(pa, ha)):.1f}   (parent {statistics.mean(pa):.1f} + helpers {statistics.mean(ha):.1f}); mean helpers per task {statistics.mean(h['n_helpers'] for h in hl):.1f}")
    for k in sorted({k for h in hl for k in h["totals"] if "token" in k}):
        print(f"helpers mean {k:30} {statistics.mean(h['totals'].get(k, 0) for h in hl):.4g}")
us = [flat(x["usage"]) for x in rows if isinstance(x.get("usage"), dict)]
if len(allrows) > len(rows):
    print(f"WARNING: {len(allrows) - len(rows)} run(s) failed at the provider and were excluded. Use --resume to redo them.")
if stopped:
    print(stopped)
print(f"reported spend this session: ${spent:.2f} (0.00 can also mean the model reports no price)")
if us:
    for k in sorted({k for u in us for k in u}):
        print(f"usage mean {k:45} {statistics.mean(u[k] for u in us if k in u):.4g}")
else:
    print("no usage data captured (add --usage-file {usage} to AGENT_CMD)")
