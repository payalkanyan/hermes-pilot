"""Validates a workflow spec and draws it as a flowchart (Mermaid) plus a context table.
  python3 workflow_tools.py invoice-matching.workflow.yaml        -> writes FLOWCHART.md next to it
Needs: pip install pyyaml"""
import sys, pathlib
try:
    import yaml
except ImportError:
    sys.exit("PyYAML is missing. Run: pip install pyyaml")

TYPES = {"tool", "agent", "code", "branch"}

def load(path):
    return yaml.safe_load(open(path, encoding="utf-8"))

def ancestors(nodes):
    """For every node id, the set of node ids that run before it."""
    parents = {n["id"]: [] for n in nodes}
    for n in nodes:
        for e in n.get("next", []):
            if e["to"] in parents:
                parents[e["to"]].append(n["id"])
    memo = {}
    def anc(i):
        if i in memo: return memo[i]
        memo[i] = set()
        out = set()
        for p in parents[i]:
            out |= {p} | anc(p)
        memo[i] = out
        return out
    return {i: anc(i) for i in parents}

def validate(spec):
    errs, warns = [], []
    nodes = spec["nodes"]; ids = [n["id"] for n in nodes]
    if len(set(ids)) != len(ids): errs.append("duplicate node ids")
    for n in nodes:
        if n.get("type") not in TYPES: errs.append(f"{n['id']}: type must be one of {sorted(TYPES)}")
        for e in n.get("next", []):
            if e["to"] not in ids: errs.append(f"{n['id']}: next points to unknown node '{e['to']}'")
    anc = ancestors(nodes)
    by_id = {n["id"]: n for n in nodes}
    known_user = set(spec.get("inputs", {}))
    # reachability from the first node
    seen, stack = set(), [ids[0]]
    while stack:
        i = stack.pop()
        if i in seen or i not in by_id: continue
        seen.add(i)
        if i in by_id: stack += [e["to"] for e in by_id[i].get("next", [])]
    for i in ids:
        if i not in seen: errs.append(f"{i}: not reachable from the first node")
    for n in nodes:
        avail = set(known_user)
        for a in anc[n["id"]]: avail |= set(by_id[a].get("outputs", []))
        loop_over = n.get("for_each")
        if loop_over:
            if loop_over not in avail: errs.append(f"{n['id']}: for_each '{loop_over}' is not produced by an earlier node")
            avail.add("item")
        ins = n.get("inputs", [])
        if n["type"] == "agent":
            if not ins: errs.append(f"{n['id']}: an agent node must declare its inputs (context is never implicit)")
            if len(ins) > 3: warns.append(f"{n['id']}: {len(ins)} inputs; is every one really needed?")
            if "output_schema" not in n: errs.append(f"{n['id']}: an agent node needs an output_schema")
            if not n.get("tools"): warns.append(f"{n['id']}: agent node with no tool allowlist")
            if not n.get("checks"): errs.append(f"{n['id']}: an agent node needs checks")
        for x in ins:
            if x in ("*", "all", "history", "context"): errs.append(f"{n['id']}: input '{x}' passes everything; declare specific inputs")
            elif x not in avail: errs.append(f"{n['id']}: input '{x}' is not available at this point (not a workflow input or an earlier node's output)")
        if n["type"] == "branch" and len(n.get("next", [])) < 2: errs.append(f"{n['id']}: a branch needs at least two routes")
        if not n.get("next") and n["id"] != ids[-1]: warns.append(f"{n['id']}: no next node (is this an end?)")
    return errs, warns

SHAPE = {"tool": ('[["', '"]]'), "agent": ('("', '")'), "code": ('["', '"]'), "branch": ('{"', '"}')}

def mermaid(spec):
    L = ["flowchart TD", '  start(["start: folder, month"])']
    for n in spec["nodes"]:
        a, b = SHAPE[n["type"]]
        loop = f"<br/>for each: {n['for_each']}" if n.get("for_each") else ""
        ctx = ", ".join(n.get("inputs", [])) or "-"
        L.append(f'  {n["id"]}{a}<b>{n["id"]}</b> ({n["type"]}){loop}<br/>gets: {ctx}{b}')
    L.append(f'  {spec["nodes"][-1]["id"]} --> finish(["final answer"])')
    L.append(f'  start --> {spec["nodes"][0]["id"]}')
    for n in spec["nodes"]:
        for e in n.get("next", []):
            lab = f'|{e["label"]}|' if e.get("label") else ""
            L.append(f'  {n["id"]} -->{lab} {e["to"]}')
    L += ["  classDef agent fill:#fff3cd,stroke:#b58900;", "  classDef code fill:#e7f1ff,stroke:#2b6cb0;",
          "  classDef tool fill:#e6ffed,stroke:#2f855a;", "  classDef branch fill:#fde8e8,stroke:#c53030;"]
    for t in TYPES:
        ids = [n["id"] for n in spec["nodes"] if n["type"] == t]
        if ids: L.append(f'  class {",".join(ids)} {t};')
    return "\n".join(L)

def table(spec):
    rows = ["| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |", "|---|---|---|---|---|---|"]
    for n in spec["nodes"]:
        ins = ", ".join(n.get("inputs", [])) or "-"
        if n.get("for_each"): ins = f"one item of `{n['for_each']}`" + (f" + {', '.join(i for i in n.get('inputs', []) if i != 'item')}" if [i for i in n.get('inputs', []) if i != 'item'] else "")
        tools = ", ".join(n.get("tools", [])) or (n.get("tool") or "-")
        rows.append(f"| {n['id']} | {n['type']} | {ins} | {tools} | {', '.join(n.get('outputs', []))} | {', '.join(str(c) for c in n.get('checks', [])) or '-'} |")
    return "\n".join(rows)

if __name__ == "__main__":
    path = pathlib.Path(sys.argv[1]); spec = load(path)
    errs, warns = validate(spec)
    for w in warns: print("warning:", w)
    for e in errs: print("ERROR:", e)
    if errs: sys.exit(1)
    out = path.parent / "FLOWCHART.md"
    out.write_text(f"# {spec['name']} workflow\n\n{spec['goal']}\n\n**Context rule:** {spec.get('context_policy', '')}.\n\n"
                   f"Legend: rounded = AI agent node, double-bordered = tool call, square = code, diamond = branch.\n\n```mermaid\n{mermaid(spec)}\n```\n\n"
                   f"## What each node receives\n\n{table(spec)}\n")
    print(f"valid: {len(spec['nodes'])} nodes. wrote {out}")
