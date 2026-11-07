"""Adds up the usage of helper agents (delegate_task children) from an exported Hermes session (markdown).
Hermes' own --usage-file report covers only the parent agent, so helper cost and calls must be added separately.
  python3 helper_usage.py exports/<session-file>.md"""
import json, sys

def flat(d, pre=""):
    out = {}
    for k, v in (d or {}).items():
        if isinstance(v, dict):
            out.update(flat(v, f"{pre}{k}."))
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            out[f"{pre}{k}"] = v
    return out

def parse_md(path):
    helpers = []
    for line in open(path, encoding="utf-8", errors="replace"):
        i = line.find('{"results"')
        if i < 0:
            continue
        try:
            obj = json.loads(line[i:].strip())
        except Exception:
            continue
        for r in obj.get("results", []):
            if isinstance(r, dict) and "task_index" in r:
                helpers.append(flat({k: v for k, v in r.items() if k != "summary"}))
    totals = {}
    for h in helpers:
        for k, v in h.items():
            if k != "task_index":
                totals[k] = round(totals.get(k, 0) + v, 6)
    return {"n_helpers": len(helpers), "totals": totals}

if __name__ == "__main__":
    r = parse_md(sys.argv[1])
    print("helpers found:", r["n_helpers"])
    for k, v in sorted(r["totals"].items()):
        print(f"  {k:32} {v}")
