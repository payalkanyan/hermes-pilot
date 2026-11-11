"""Validates a workflow spec and draws it as a flowchart (Mermaid) plus a context table.
  python3 workflow_tools.py invoice-matching.workflow.yaml        -> writes FLOWCHART.md next to it
Needs: pip install pyyaml"""
import sys, pathlib
try:
    import yaml
except ImportError:
    sys.exit("PyYAML is missing. Run: pip install pyyaml")

TYPES = {"tool", "agent", "code", "branch"}
# Checks the runner knows how to execute itself. Anything else is a custom check and needs a
# one-line rule in the spec's check_descriptions, so a judge node can actually run it.
BUILTIN_CHECKS = {"schema", "non_empty", "grounded_in_tool_results", "readback_matches_total",
                  "one_verdict_per_invoice", "reasons_are_bare_codes"}

def hermes_tools(repo=None):
    """Official Hermes tool names, read from the repo's toolsets.py. Returns None if it cannot be read
    (then tool names are not checked, rather than being wrongly rejected)."""
    import os, pathlib as _p, re as _re
    cands = [repo] if repo else []
    cands += [os.environ.get("HERMES_REPO"), _p.Path.home() / "projects/hermes-agent", _p.Path.home() / ".hermes/hermes-agent"]
    for c in cands:
        if not c: continue
        f = _p.Path(c) / "toolsets.py"
        if f.exists():
            names = set(_re.findall(r'"([a-z][a-z0-9_]{2,40})"', f.read_text(encoding="utf-8", errors="replace")))
            return names or None
    return None

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

def validate(spec, tool_names=None):
    errs, warns = [], []
    tool_names = tool_names if tool_names is not None else hermes_tools()
    described = set((spec.get("check_descriptions") or {}))
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
        for t in n.get("tools", []) + ([n["tool"]] if n.get("tool") else []):
            if tool_names and t not in tool_names and t not in set(spec.get("tools_provided") or []):
                warns.append(f"UNKNOWN TOOL {n['id']}: '{t}' is not in Hermes' toolsets.py and is not declared under tools_provided (an MCP tool, or invented?)")
        for c in n.get("checks", []):
            cname = c.split(":")[0].strip() if isinstance(c, str) else str(c)
            if cname not in BUILTIN_CHECKS and cname not in described:
                errs.append(f"{n['id']}: check '{cname}' is not built in, so add a one-line rule for it under check_descriptions")
        for x in ins:
            if x in ("*", "all", "history", "context"): errs.append(f"{n['id']}: input '{x}' passes everything; declare specific inputs")
            elif x not in avail: errs.append(f"{n['id']}: input '{x}' is not available at this point (not a workflow input or an earlier node's output)")
        risky = {"terminal", "patch", "write_file", "browser_exec", "skill_manage"}
        used = set(n.get("tools", [])) | ({n["tool"]} if n.get("tool") else set())
        if used & risky:
            direct = [p["id"] for p in nodes for e in p.get("next", []) if e["to"] == n["id"]]
            gated = bool(n.get("checks")) or any(by_id[p]["type"] == "branch" for p in direct)
            if not gated:
                errs.append(f"{n['id']}: uses {sorted(used & risky)} but nothing checks or approves before it runs")
        if n["type"] == "branch" and len(n.get("next", [])) < 2: errs.append(f"{n['id']}: a branch needs at least two routes")
        if not n.get("next") and n["id"] != ids[-1]: warns.append(f"{n['id']}: no next node (is this an end?)")
    return errs, warns

SHAPE = {"tool": ('[["', '"]]'), "agent": ('("', '")'), "code": ('["', '"]'), "branch": ('{"', '"}')}

def mermaid(spec):
    L = ["flowchart TD", f'  start(["start: {", ".join(spec.get("inputs", {})) or "inputs"}"])']
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
