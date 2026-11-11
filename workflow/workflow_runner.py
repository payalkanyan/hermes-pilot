"""Runs a workflow spec node by node. Each node receives ONLY the inputs it declares (no history, no other nodes' output).
Agent nodes run as a fresh Hermes one-shot session per item; tool and code nodes run as plain code.
  python3 workflow_runner.py invoice-matching.workflow.yaml --task T01 --mode code      # stand-in agent (no model, free)
  AGENT_CMD='hermes -z {prompt} --usage-file {usage} --provider ... -m ... --ignore-rules' \\
  python3 workflow_runner.py invoice-matching.workflow.yaml --all --mode hermes        # real model
Writes a per-node trace (inputs, outputs, checks, time, usage) to results/graph-traces/."""
import argparse, concurrent.futures as cf, json, os, pathlib, shlex, statistics, subprocess, sys, tempfile, time
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
import world_api as W
from grade import grade, load_calls, extract_json, REASONS
from workflow_tools import load, validate, BUILTIN_CHECKS

class StepFailed(Exception): pass

def check_schema(obj, sch, path="$"):
    t, errs = sch.get("type"), []
    if t == "object":
        if not isinstance(obj, dict): return [f"{path}: expected an object"]
        errs += [f"{path}.{k}: missing" for k in sch.get("required", []) if k not in obj]
        props = sch.get("properties", {})
        if sch.get("additionalProperties") is False:
            errs += [f"{path}.{k}: not allowed" for k in obj if k not in props]
        for k, v in props.items():
            if k in obj: errs += check_schema(obj[k], v, f"{path}.{k}")
    elif t == "array":
        if not isinstance(obj, list): return [f"{path}: expected an array"]
        for i, x in enumerate(obj): errs += check_schema(x, sch.get("items", {}), f"{path}[{i}]")
    elif t == "string" and not isinstance(obj, str): errs.append(f"{path}: expected a string")
    elif t == "number" and (isinstance(obj, bool) or not isinstance(obj, (int, float))): errs.append(f"{path}: expected a number")
    elif t == "boolean" and not isinstance(obj, bool): errs.append(f"{path}: expected true or false")
    return errs

def canon(x):
    if isinstance(x, bool): return x
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, dict): return {k: canon(v) for k, v in x.items()}
    if isinstance(x, list): return [canon(v) for v in x]
    return x

def truth_fact(iid):
    """What the tools really say about one invoice (the runner's own ground truth for the grounding check)."""
    inv = W.get_invoice(iid)
    if "error" in inv: return None
    po, dl = W.get_purchase_order(inv["po_ref"]), W.get_deliveries(inv["po_ref"])
    found = "error" not in po
    return {"invoice_id": iid, "supplier": inv["supplier"], "number": inv["number"], "date": inv["date"], "po_id": inv["po_ref"],
            "inv_lines": inv["lines"], "tax": inv["tax"], "total": inv["total"], "po_found": found,
            "po_lines": po["lines"] if found else [], "delivered": [] if isinstance(dl, dict) else [l for r in dl for l in r["lines"]]}

def fact_problems(got, want):
    bad = []
    for k in want:
        g, w = canon(got.get(k)), canon(want[k])
        if isinstance(w, list): g = sorted(json.dumps(x, sort_keys=True) for x in (g or [])); w = sorted(json.dumps(x, sort_keys=True) for x in w)
        if g != w: bad.append(k)
    return [f"field '{k}' does not match what the tools returned" for k in bad]

def call_hermes(prompt, usage_dir, tag):
    usage = usage_dir / f"{tag}.json"
    cmd = os.environ["AGENT_CMD"].replace("{prompt}", shlex.quote(prompt)).replace("{usage}", shlex.quote(str(usage)))
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1800).stdout
    u = None
    try: u = json.loads(usage.read_text())
    except Exception: pass
    return out, u

def run_agent_item(node, item, mode, schema, usage_dir, usages):
    truth = truth_fact(item)
    if mode == "code":                       # stand-in for a perfect agent: lets us test the graph without a model
        return truth
    prompt = (f"{node['goal']}\n\n{node.get('instructions', '')}\n\nYou are one step of an automated workflow and you only know the input below. "
              f"Use only these tools: {', '.join(node.get('tools', []))}.\nInput: {json.dumps({'invoice_id': item})}\n"
              f"Reply with ONLY one JSON object matching this JSON schema, with no other text:\n{json.dumps(schema)}")
    last = []
    for attempt in range(node.get("on_fail", {}).get("retry", 0) + 1):
        text, u = call_hermes(prompt, usage_dir, f"{node['id']}-{item}-a{attempt}")
        if u: usages.append(u)
        obj = extract_json(text)
        last = check_schema(obj, schema) if obj is not None else ["no JSON object found in the reply"]
        if not last and "grounded_in_tool_results" in node.get("checks", []): last = fact_problems(obj, truth)
        if not last: return obj
        prompt += f"\n\nYour previous reply was rejected: {'; '.join(last[:6])}. Fix it and reply with ONLY the JSON object."
    raise StepFailed(f"{node['id']} {item}: {'; '.join(last[:4])}")

def tool_item(node, scoped, item):
    name = node["tool"]
    if name == "list_invoices": return [x["invoice_id"] for x in W.list_invoices(scoped["folder"])]
    if name == "create_draft_bill":
        r = W.create_draft_bill(item["invoice_id"], item["po_id"], item["total"])
        if "error" in r: raise StepFailed(f"create_draft_bill {item['invoice_id']}: {r['error']}")
        return {"draft_id": r["draft_id"], **item}
    if name == "get_draft_bill":
        r = W.get_draft_bill(item["draft_id"])
        if "error" in r or abs(r["total"] - item["total"]) > 0.005: raise StepFailed(f"read-back mismatch for {item['draft_id']}")
        return {"invoice_id": item["invoice_id"], "po_id": item["po_id"], "draft_id": item["draft_id"]}
    raise StepFailed(f"unknown tool {name}")

def run_code(node, scoped):
    p = subprocess.run([sys.executable, str(HERE / node["script"])], input=json.dumps({"inputs": scoped}), capture_output=True, text=True)
    if p.returncode != 0: raise StepFailed(f"{node['id']} script failed: {p.stderr.strip()[-300:]}")
    return json.loads(p.stdout)

def run_branch(node, scoped):
    facts = {f["invoice_id"]: f for f in scoped["facts"]}
    ok, other = [], []
    for v in scoped["verdicts"]:
        (ok if v["verdict"] == "ok" else other).append(v)
    return {"ok_items": [{"invoice_id": v["invoice_id"], "po_id": facts[v["invoice_id"]]["po_id"], "total": facts[v["invoice_id"]]["total"]} for v in ok],
            "exception_items": other}

def judge(rule, node_id, out, mode):
    """A custom check: a separate model call that sees ONLY the rule and this node's output."""
    if mode == "code":
        return True, "judge skipped in code mode"
    prompt = ("You are grading one step of an automated workflow. Answer with ONLY one JSON object: "
              '{"pass": true or false, "why": "one short sentence"}.\n'
              f"RULE THAT MUST HOLD: {rule}\nSTEP OUTPUT:\n{json.dumps(out)[:12000]}")
    text, _ = call_hermes(prompt, pathlib.Path(tempfile.mkdtemp()), f"judge-{node_id}")
    v = extract_json(text) or {}
    return bool(v.get("pass")), str(v.get("why", "judge gave no verdict"))

def node_checks(node, scoped, items, out, spec=None, mode="code"):
    names = node.get("checks", [])
    descs = (spec or {}).get("check_descriptions") or {}
    for c in names:
        if c in ("schema", "grounded_in_tool_results", "readback_matches_total"): continue   # done where the data is produced
        if c == "non_empty":
            if not all(out[k] for k in node["outputs"]): raise StepFailed(f"{node['id']}: check non_empty failed")
        elif c == "one_verdict_per_invoice":
            if [v["invoice_id"] for v in out["verdicts"]] != [f["invoice_id"] for f in scoped["facts"]]: raise StepFailed("decide: not exactly one verdict per invoice")
        elif c == "reasons_are_bare_codes":
            bad = [e for e in out["final_answer"]["exceptions"] if e["reason"] not in REASONS]
            if bad: raise StepFailed(f"report: reasons are not bare codes: {bad[:2]}")
        elif c in descs:
            ok, why = judge(descs[c], node["id"], out, mode)
            if not ok: raise StepFailed(f"{node['id']}: check '{c}' failed the judge: {why}")
        else:
            raise StepFailed(f"{node['id']}: unknown check '{c}' and no rule for it in check_descriptions")

def run_workflow(spec, inputs, mode, usage_dir):
    store, trace, usages = dict(inputs), [], []
    for node in spec["nodes"]:
        t0 = time.time()
        declared = node.get("inputs", [])
        scoped = {k: store[k] for k in declared if k != "item"}      # ONLY declared inputs; anything else raises KeyError
        items = store[node["for_each"]] if node.get("for_each") else None
        node_usages = []
        try:
            if node["type"] == "agent":
                schema = node["output_schema"] if isinstance(node["output_schema"], dict) else json.load(open(HERE / node["output_schema"]))
                with cf.ThreadPoolExecutor(max_workers=node.get("parallel", 1)) as ex:
                    res = list(ex.map(lambda it: run_agent_item(node, it, mode, schema, usage_dir, node_usages), items))
                out = {node["outputs"][0]: res}
            elif node["type"] == "tool":
                if items is None: out = {node["outputs"][0]: tool_item(node, scoped, None)}
                else: out = {node["outputs"][0]: [tool_item(node, scoped, it) for it in items]}
            elif node["type"] == "code": out = run_code(node, scoped)
            elif node["type"] == "branch": out = run_branch(node, scoped)
            if set(out) != set(node["outputs"]): raise StepFailed(f"{node['id']}: produced {sorted(out)} but declared {node['outputs']}")
            node_checks(node, scoped, items, out, spec, mode)
        except StepFailed as e:
            trace.append({"node": node["id"], "status": "FAILED", "error": str(e), "input_keys": sorted(declared)})
            raise
        store.update(out); usages += node_usages
        trace.append({"node": node["id"], "type": node["type"], "status": "ok", "input_keys": sorted(declared), "n_items": len(items) if items is not None else None,
                      "input_chars": len(json.dumps(scoped, default=str)) + (len(json.dumps(items, default=str)) if items else 0),
                      "output_chars": len(json.dumps(out, default=str)), "seconds": round(time.time() - t0, 2), "model_calls": len(node_usages)})
    return store["final_answer"], trace, usages

def usage_totals(usages):
    t = lambda u, k: ((u.get("total_including_auxiliary") or {}).get(k) or 0)
    return {"cost": sum(t(u, "estimated_cost_usd") for u in usages), "api_calls": sum(t(u, "api_calls") for u in usages),
            "sessions": len(usages), "largest_session_input_tokens": max([u.get("input_tokens") or 0 for u in usages] or [0])}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--mode", choices=["code", "hermes"], default="code")
    ap.add_argument("--task"); ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    spec = load(a.spec); errs, warns = validate(spec)
    if errs: sys.exit("spec invalid:\n  " + "\n  ".join(errs))
    tasks = [json.loads(l) for l in open(ROOT / "data" / "tasks.jsonl")]
    tasks = [t for t in tasks if a.all or t["task_id"] == a.task]
    if not tasks: sys.exit("give --task T01 or --all")
    tdir = ROOT / "results" / "graph-traces"; tdir.mkdir(parents=True, exist_ok=True)
    udir = pathlib.Path(tempfile.mkdtemp(prefix="graph-usage-"))
    rows = []
    for t in tasks:
        W.reset(); t0 = time.time(); err = None
        try:
            final, trace, usages = run_workflow(spec, {"folder": t["folder"], "month": t["month"]}, a.mode, udir)
        except StepFailed as e:
            final, usages, err = {}, [], str(e)
            trace = [{"error": err}]
        g = grade(t, json.dumps(final), W._state(), load_calls(W.LOG), W.WORLD)
        g.update(seconds=round(time.time() - t0, 1), error=err, **usage_totals(usages))
        rows.append(g)
        (tdir / f"{t['task_id']}-{a.mode}.trace.jsonl").write_text("".join(json.dumps(x) + "\n" for x in trace))
        print(f"{t['task_id']}  {'PASS' if g['success'] else 'FAIL'}  {g['seconds']}s" + (f"  {err}" if err else ""))
    n = len(rows)
    print(f"\ntasks passed (strict)  {sum(r['success'] for r in rows)}/{n}\nsystem state correct   {sum(r['outcome_correct'] for r in rows)}/{n}\ninvented fields        {sum(r['fields_ungrounded'] for r in rows)}")
    if a.mode == "hermes":
        print(f"mean all-in cost/task  ${statistics.mean(r['cost'] for r in rows):.4f}\nmean model calls/task  {statistics.mean(r['api_calls'] for r in rows):.1f}\n"
              f"largest input tokens in any one node session  {max(r['largest_session_input_tokens'] for r in rows)}")
    print(f"traces in {tdir}")
