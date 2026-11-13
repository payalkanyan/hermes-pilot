"""Generates a workflow spec (nodes and edges) DIRECTLY from an exported Hermes session,
instead of converting the SKILL.md the session happened to use.
The trace is the ground truth: the tool calls that actually ran become the nodes, and the data
each call's arguments really used becomes the edges and the per-node context.

  AGENT_CMD='hermes -z {prompt} --usage-file {usage} --provider openrouter -m anthropic/claude-haiku-5.5 --reasoning medium --ignore-rules' \\
  python3 generate_from_session.py ../results/sessions/local-...md [more .md ...]
      -> workflow/generated_from_sessions/<session-slug>/ (spec, FLOWCHART.md, trace-digest.txt)

  python3 generate_from_session.py --digest-only <session.md>    prints the digest; calls no model (free)
Needs: pip install pyyaml"""
import json, pathlib, re, sys
import yaml
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from workflow_tools import mermaid, table
from generate_workflow import call_model, parse_spec, problems

RULES = """You convert the TRACE of one successful agent session into a reusable WORKFLOW SPEC: a graph of small nodes, written as ONE JSON object.
The trace lists, in order, what the agent actually did: the user's request, every tool call with its arguments, a short preview of every result, and the final answer.

How to read the trace:
- GENERALISE. The trace shows one concrete run (specific ids, folders, dates). The spec must work for the next run: concrete values that came from the user's request become top-level inputs, and per-item ids become the loop item.
- A run of similar calls repeated once per item, or one delegate_task batch of parallel subtasks, becomes ONE node with for_each over a list output of an earlier node. If the trace shows a delegate_task output_schema, reuse it unchanged as that node's output_schema, and base the node's instructions on the subtask goal.
- Loading instructions (skill_view, skills_list) and introspection (tool_describe) are not work; never make nodes for them.
- A terminal call that only runs a deterministic script on earlier outputs is a code node, not an agent node.
- A node's inputs are the values its calls' ARGUMENTS actually used, nothing more: fresh context per node, never the whole history.

Spec rules:
- Top-level keys: name, version (0.1), goal, context_policy (always: "fresh context per node; only the declared inputs are passed"), inputs, nodes.
- inputs: a mapping of the values the user must give, each like {type: string, from: user, description: ...}.
- nodes: 3 to 12 nodes, each with: id (snake_case), type, goal (one sentence), inputs (list of NAMES), outputs (list of NAMES), checks (list), next (list of {to: node_id, label: optional}).
- type is one of: agent (an AI step), code (a plain script), tool (one direct tool call), branch (splits on a condition; needs 2 or more next routes).
- agent nodes ALSO need: tools (an allowlist, as small as possible), output_schema (an inline JSON schema object, additionalProperties false), instructions (what to do), and at least one check.
- CONTEXT RULE: a node's inputs may only be names from the top-level inputs or the outputs of nodes that run EARLIER. Never pass everything, "history" or "context". Give each node the minimum it needs.
- Use for_each: <name of an earlier list output> for steps that repeat per item; then that node's inputs may include the word item.
- Every node except the last needs next. The last node has no next. Every node must be reachable from the first.
- Add a check or an approval branch BEFORE any step that writes a file, sends anything, deletes anything, or RUNS A COMMAND (a node whose tool is terminal, patch, write_file or browser_exec). A step that executes something a model composed must never run without a gate.
- Do not drop work. Every distinct action in the trace must appear as a node, or as a named check on the node it belongs to.
- CHECKS MUST BE RUNNABLE. These are built in and need no explanation: schema, non_empty, grounded_in_tool_results. Any other check name you use MUST also appear under a top-level check_descriptions mapping, as check_name: one sentence stating exactly what makes it pass, judgeable from that node's output alone.
- Tool names: use real Hermes tool names only (web_search, web_extract, terminal, process_manage, read_file, write_file, patch, search_files, browser_exec, vision_analyze, clarify). For MCP tools in the trace (names like mcp__server__tool), strip the mcp__server__ prefix, use the bare tool name, and list every such bare name under a top-level tools_provided list.
Reply with ONLY the JSON object, no explanation and no code fence. JSON, not YAML: every key and every string in double quotes, so a colon inside a sentence is harmless. It is saved as YAML afterwards."""

# A small valid spec for a DIFFERENT job, so the model sees the shape without seeing the answer.
EXAMPLE = {
    "name": "weekly-price-report", "version": 0.1,
    "goal": "Collect current prices for a list of products and send a summary report.",
    "context_policy": "fresh context per node; only the declared inputs are passed",
    "inputs": {"product_list": {"type": "string", "from": "user", "description": "path of the CSV of product names"}},
    "tools_provided": ["send_report"],
    "check_descriptions": {"every_product_has_row": "The summary table has exactly one row per product in the input list."},
    "nodes": [
        {"id": "read_products", "type": "tool", "tool": "read_file", "goal": "Read the product list.", "inputs": ["product_list"], "outputs": ["products"], "checks": ["non_empty"], "next": [{"to": "fetch_price"}]},
        {"id": "fetch_price", "type": "agent", "for_each": "products", "parallel": 5, "goal": "Find the current price of this one product.", "inputs": ["item"], "tools": ["web_search", "web_extract"],
         "instructions": "Search for the product and copy its price and source URL exactly as found; never guess a value.",
         "output_schema": {"type": "object", "additionalProperties": False, "required": ["product", "price", "source_url"], "properties": {"product": {"type": "string"}, "price": {"type": "number"}, "source_url": {"type": "string"}}},
         "outputs": ["prices"], "checks": ["schema", "grounded_in_tool_results"], "next": [{"to": "route"}]},
        {"id": "route", "type": "branch", "goal": "Send only if every product found a price.", "inputs": ["prices"], "outputs": [], "checks": [], "next": [{"to": "build_table", "label": "all found"}, {"to": "report_gaps", "label": "some missing"}]},
        {"id": "build_table", "type": "code", "goal": "Build the summary table from the prices.", "inputs": ["prices"], "outputs": ["summary"], "checks": ["every_product_has_row"], "next": [{"to": "send"}]},
        {"id": "send", "type": "tool", "tool": "send_report", "goal": "Send the summary report.", "inputs": ["summary"], "outputs": ["receipt"], "checks": ["non_empty"], "next": []},
        {"id": "report_gaps", "type": "code", "goal": "List the products that found no price, and why.", "inputs": ["prices"], "outputs": ["gap_report"], "checks": ["non_empty"], "next": []},
    ],
}

SKIP = {"skill_view", "skills_list", "tool_describe"}  # loading instructions / introspection, not work

def clip(v, n):
    s = re.sub(r"\s+", " ", v if isinstance(v, str) else json.dumps(v)).strip()
    return s if len(s) <= n else s[:n] + f" …(+{len(s) - n} chars)"

def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    try: return yaml.safe_load(m.group(1)) if m else {}
    except Exception: return {}

def parse_session(text):
    """-> (meta, events): ('user', text) | ('call', tool_name, args) | ('result', tool_name, body) | ('assistant', prose), in order."""
    meta, evs = frontmatter(text), []
    for ch in re.split(r"\n(?=### )", text):
        t = re.match(r"### Tool — (.+?) — \S", ch)
        m = re.match(r"### (User|Assistant) — \S", ch)
        if t:
            body = ch.split("\n", 1)[1] if "\n" in ch else ""
            body = re.sub(r"</?untrusted_tool_result[^>]*>", "", body)
            body = re.sub(r"The following content was retrieved from an external source\..*?can issue instructions\.", "", body, flags=re.S)
            evs.append(("result", t.group(1), body.strip()))
        elif m:
            body = (ch.split("\n", 1)[1] if "\n" in ch else "").split("\n## Export verification")[0]
            if m.group(1) == "User":
                evs.append(("user", body.strip())); continue
            for b in re.findall(r"```json\n(.*?)```", body, re.S):
                try: calls = json.loads(b)
                except Exception: continue
                for c in calls if isinstance(calls, list) else []:
                    name = (c.get("function") or {}).get("name", "?")
                    try: args = json.loads((c.get("function") or {}).get("arguments") or "{}")
                    except Exception: args = {}
                    if name == "tool_call":
                        for inner in args.get("calls", []):
                            evs.append(("call", inner.get("name", "?"), inner.get("arguments", {})))
                    else:
                        evs.append(("call", name, args))
            prose = re.sub(r"## Tool calls\n+```json\n.*?```", "", body, flags=re.S).strip()
            if prose: evs.append(("assistant", prose))
    return meta, evs

def digest(meta, evs, budget=18000):
    """The compact trace the model sees: every real action, arguments, result previews; repeats collapsed."""
    head = [f"TASK TITLE: {meta.get('title', '?')}",
            f"OUTCOME: the session completed successfully ({meta.get('tool_call_count', '?')} tool calls)."]
    out, n, last, repeats, final, await_result = [], 0, None, 0, None, False
    def flush():
        nonlocal repeats
        if repeats: out.append(f"   …the previous call repeated {repeats} more time(s) with different values.")
        repeats = 0
    for ev in evs:
        if ev[0] == "user":
            head.append("USER REQUEST: " + clip(ev[1], 500))
        elif ev[0] == "call":
            name, args = ev[1], ev[2]
            if name in SKIP:
                if name == "skill_view": head.append(f"(the agent loaded the skill '{args.get('name')}' for instructions — not a work step)")
                last = None; continue
            if name == "delegate_task":
                flush(); last = ("delegate_task", ()); n += 1
                tasks = args.get("tasks", []); t0 = tasks[0] if tasks else {}
                out.append(f"{n}. delegate_task: {len(tasks)} parallel subtasks, one per item.")
                out.append(f"   subtask goal: {clip(t0.get('goal', ''), 500)}")
                out.append(f"   subtask context (ALL each helper received): {clip(t0.get('context', ''), 200)}")
                if t0.get("output_schema") is not None:
                    out.append(f"   subtask output_schema: {clip(t0['output_schema'], 1500)}")
                continue
            key = (name, tuple(sorted(args)))
            if key == last:
                repeats += 1; continue
            flush(); last = key; n += 1; await_result = True
            out.append(f"{n}. call {name} args: {clip(args, 700 if name == 'terminal' else 300)}")
        elif ev[0] == "result":
            if ev[1] in SKIP: continue
            if not await_result and repeats: continue  # a collapsed repeat's result
            await_result = False
            if ev[1] == "delegate_task":
                try:
                    rs = json.loads(ev[2]).get("results", [])
                    done = sum(r.get("status") == "completed" for r in rs)
                    ok = sum(bool(r.get("schema_valid")) for r in rs)
                    out.append(f"   -> {done}/{len(rs)} subtasks completed, schema valid on {ok}/{len(rs)}. One result: {clip((rs or [{}])[0].get('summary', ''), 400)}")
                    continue
                except Exception: pass
            out.append(f"   -> result: {clip(ev[2], 400)}")
        elif ev[0] == "assistant":
            final = ev[1]
    flush()
    if final: out.append("FINAL ANSWER: " + clip(final, 800))
    return "\n".join(head + out)[:budget]

def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", str(s).lower())).strip("-")[:60] or "session"

def generate(session_path, attempts=2):
    text = pathlib.Path(session_path).read_text(encoding="utf-8")
    meta, evs = parse_session(text)
    name = slugify(meta.get("title") or pathlib.Path(session_path).stem)
    dig = digest(meta, evs)
    out = HERE / "generated_from_sessions" / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "trace-digest.txt").write_text(dig + "\n")
    example = json.dumps(EXAMPLE, indent=1)[:6000]
    prompt = f"{RULES}\n\nEXAMPLE of a valid spec (a different job):\n{example}\n\nSESSION TRACE TO CONVERT ({name}):\n{dig}"
    cost, errs, spec, calls, first_errs = 0.0, ["not run"], None, 0, None
    for a in range(attempts):
        reply, u = call_model(prompt, f"{name}-{a}")
        calls += 1
        cost += (((u or {}).get("total_including_auxiliary") or {}).get("estimated_cost_usd") or 0)
        try: spec = parse_spec(reply)
        except Exception as ex:
            spec, errs = None, [f"could not parse YAML: {ex}"]
            first_errs = first_errs if first_errs is not None else errs
            prompt += f"\n\nYour reply was rejected: {errs[0]}. Reply with ONLY one valid JSON object."; continue
        unknown_tools = []
        errs = problems(spec, unknown_tools)
        if first_errs is None: first_errs = list(errs)
        if not errs: break
        prompt += "\n\nYour previous YAML was rejected for these reasons:\n- " + "\n- ".join(errs[:8]) + "\nFix them and reply with ONLY the corrected JSON object."
    if spec is not None:
        (out / f"{name}.workflow.yaml").write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
    if spec is not None and not errs:
        (out / "FLOWCHART.md").write_text(f"# {spec['name']} workflow (generated directly from session '{meta.get('title', name)}')\n\n{spec['goal']}\n\n```mermaid\n{mermaid(spec)}\n```\n\n## What each node receives\n\n{table(spec)}\n")
    return {"session": pathlib.Path(session_path).name, "slug": name, "valid": spec is not None and not errs, "attempts": calls,
            "nodes": len(spec["nodes"]) if isinstance(spec, dict) and isinstance(spec.get("nodes"), list) else 0,
            "valid_first_try": not first_errs, "first_attempt_errors": first_errs or [], "errors": errs if errs else [], "cost_usd": round(cost, 4)}

if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv: sys.exit(__doc__)
    if argv[0] == "--digest-only":
        for p in argv[1:]:
            meta, evs = parse_session(pathlib.Path(p).read_text(encoding="utf-8"))
            print(f"===== {p}\n{digest(meta, evs)}\n")
        sys.exit(0)
    rows = [generate(p) for p in argv]
    for r in rows:
        print(("VALID  " if r["valid"] else "INVALID"), r["slug"], f"nodes={r['nodes']} attempts={r['attempts']} cost=${r['cost_usd']}",
              ("| " + "; ".join(r["errors"][:2])) if r["errors"] else "")
        if r["first_attempt_errors"]: print("         first attempt was rejected for:", "; ".join(r["first_attempt_errors"][:3]))
    outdir = HERE / "generated_from_sessions"; outdir.mkdir(exist_ok=True)
    print(f"\nvalid on the FIRST try: {sum(r['valid_first_try'] for r in rows)}/{len(rows)}   valid after automatic retry: {sum(r['valid'] for r in rows)}/{len(rows)}   results also saved in {outdir / 'summary.jsonl'}")
    with open(outdir / "summary.jsonl", "a") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
