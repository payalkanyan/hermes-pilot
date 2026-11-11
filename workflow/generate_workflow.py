"""Turns an existing SKILL.md into a workflow spec (nodes and edges), checks it, and draws the flowchart.
Hermes already writes a skill after a successful task; this converts that skill into a workflow.
  AGENT_CMD='hermes -z {prompt} --usage-file {usage} --provider openrouter -m anthropic/claude-haiku-5.5 --ignore-rules' \\
  python3 generate_workflow.py path/to/SKILL.md [more SKILL.md ...]     -> workflow/generated/<skill>/ (spec, FLOWCHART.md)
Needs: pip install pyyaml"""
import json, os, pathlib, re, shlex, subprocess, sys, tempfile
import yaml
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from workflow_tools import validate, mermaid, table

RULES = """You convert a skill (written instructions for an AI agent) into a WORKFLOW SPEC: a graph of small nodes, written as ONE JSON object.
Rules:
- Top-level keys: name, version (0.1), goal, context_policy (always: "fresh context per node; only the declared inputs are passed"), inputs, nodes.
- inputs: a mapping of the values the user must give, each like {type: string, from: user, description: ...}.
- nodes: 3 to 12 nodes, each with: id (snake_case), type, goal (one sentence), inputs (list of NAMES), outputs (list of NAMES), checks (list), next (list of {to: node_id, label: optional}).
- type is one of: agent (an AI step), code (a plain script), tool (one direct tool call), branch (splits on a condition; needs 2 or more next routes).
- agent nodes ALSO need: tools (an allowlist of tool names, as small as possible), output_schema (an inline JSON schema object, additionalProperties false), instructions (what to do), and at least one check.
- CONTEXT RULE: a node's inputs may only be names from the top-level inputs or the outputs of nodes that run EARLIER. Never pass everything, "history" or "context". Give each node the minimum it needs.
- Use for_each: <name of an earlier list output> for steps that repeat per item; then that node's inputs may include the word item.
- Every node except the last needs next. The last node has no next. Every node must be reachable from the first.
- Add a check or an approval branch BEFORE any step that writes a file, sends anything, deletes anything, or RUNS A COMMAND (a node whose tool is terminal, patch, write_file or browser_exec). A node that executes something a model just composed must never be reached without a gate.
- Do not drop steps. Every numbered step, phase or rule in the skill must appear as a node, or as a named check on the node it belongs to. If a step is a quality requirement rather than an action (for example "preserve the meaning"), make it a check with a rule in check_descriptions.
- CHECKS MUST BE RUNNABLE. These are built in and need no explanation: schema, non_empty, grounded_in_tool_results. Any other check name you use MUST also appear under a top-level check_descriptions mapping, as check_name: one sentence stating exactly what makes it pass, judgeable from that node's output alone. Example: check_descriptions: {tests_fail_first: "The test output shows the new test failing before any fix is applied."}
- Use ONLY real Hermes tool names: web_search, web_extract, terminal, process_manage, read_file, write_file, patch, search_files, skills_list, skill_view, skill_manage, browser_exec, vision_analyze, clarify. If the skill needs a tool outside that list, list its name under a top-level tools_provided list.
Reply with ONLY the JSON object, no explanation and no code fence. JSON, not YAML: every key and every string in double quotes, so a colon inside a sentence is harmless. It is saved as YAML afterwards."""

def call_model(prompt, tag):
    usage = pathlib.Path(tempfile.mkdtemp()) / f"{tag}.json"
    cmd = os.environ["AGENT_CMD"].replace("{prompt}", shlex.quote(prompt)).replace("{usage}", shlex.quote(str(usage)))
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=900).stdout
    try: u = json.loads(usage.read_text())
    except Exception: u = None
    return out, u

def parse_spec(text):
    """Accepts a JSON object (preferred) or YAML; yaml.safe_load reads both."""
    m = re.search(r"```(?:json|yaml|yml)?\n(.*?)```", text, re.S)
    body = m.group(1) if m else text
    i, j = body.find("{"), body.rfind("}")
    if i != -1 and j > i:
        try: return json.loads(body[i:j + 1])
        except Exception: pass
    return yaml.safe_load(body)

def problems(spec, unknown_tools):
    if not isinstance(spec, dict) or not isinstance(spec.get("nodes"), list) or not spec["nodes"]:
        return ["the reply is not a YAML mapping with a non-empty 'nodes' list"]
    errs = [f"missing top-level key '{k}'" for k in ("name", "goal", "inputs") if k not in spec]
    if len(spec["nodes"]) > 12: errs.append("more than 12 nodes; merge steps")
    try:
        e, w = validate(spec); errs += e; unknown_tools.extend(x for x in w if x.startswith("UNKNOWN TOOL"))
    except Exception as ex:
        errs.append(f"structure error: {type(ex).__name__}: {ex}")
    return errs

def generate(skill_path, example_text, attempts=2):
    skill = pathlib.Path(skill_path).read_text(encoding="utf-8")[:24000]
    name = pathlib.Path(skill_path).resolve().parent.name
    prompt = f"{RULES}\n\nEXAMPLE of a valid spec (a different job):\n{example_text}\n\nSKILL TO CONVERT ({name}):\n{skill}"
    cost, errs, spec, calls, first_errs = 0.0, ["not run"], None, 0, None
    for a in range(attempts):
        text, u = call_model(prompt, f"{name}-{a}")
        calls += 1
        cost += (((u or {}).get("total_including_auxiliary") or {}).get("estimated_cost_usd") or 0)
        try: spec = parse_spec(text)
        except Exception as ex:
            spec, errs = None, [f"could not parse YAML: {ex}"]
            first_errs = first_errs if first_errs is not None else errs
            prompt += f"\n\nYour reply was rejected: {errs[0]}. Reply with ONLY one valid JSON object."; continue
        unknown_tools = []
        errs = problems(spec, unknown_tools)
        if first_errs is None: first_errs = list(errs)
        if not errs: break
        prompt += "\n\nYour previous YAML was rejected for these reasons:\n- " + "\n- ".join(errs[:8]) + "\nFix them and reply with ONLY the corrected JSON object."
    out = HERE / "generated" / name
    out.mkdir(parents=True, exist_ok=True)
    if spec is not None:
        (out / f"{name}.workflow.yaml").write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
    if spec is not None and not errs:
        (out / "FLOWCHART.md").write_text(f"# {spec['name']} workflow (generated from the {name} skill)\n\n{spec['goal']}\n\n```mermaid\n{mermaid(spec)}\n```\n\n## What each node receives\n\n{table(spec)}\n")
    return {"skill": name, "valid": spec is not None and not errs, "attempts": calls, "nodes": len(spec["nodes"]) if isinstance(spec, dict) and isinstance(spec.get("nodes"), list) else 0,
            "unknown_tools": unknown_tools if spec is not None else [], "valid_first_try": not first_errs, "first_attempt_errors": first_errs or [], "errors": errs if errs else [], "cost_usd": round(cost, 4)}

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    example = json.dumps(yaml.safe_load((HERE / "invoice-matching.workflow.yaml").read_text()), indent=1)[:6000]
    rows = [generate(p, example) for p in sys.argv[1:]]
    for r in rows:
        print(("VALID  " if r["valid"] else "INVALID"), r["skill"], f"nodes={r['nodes']} attempts={r['attempts']} cost=${r['cost_usd']}", ("| " + "; ".join(r["errors"][:2])) if r["errors"] else "")
        if r.get("unknown_tools"): print("         " + "; ".join(x.replace("UNKNOWN TOOL ", "unknown tool in ") for x in r["unknown_tools"][:2]))
        if r["first_attempt_errors"]: print("         first attempt was rejected for:", "; ".join(r["first_attempt_errors"][:3]))
    print(f"\nvalid on the FIRST try: {sum(r['valid_first_try'] for r in rows)}/{len(rows)}   valid after automatic retry: {sum(r['valid'] for r in rows)}/{len(rows)}   results also saved in {HERE / 'generated' / 'summary.jsonl'}")
    (HERE / "generated").mkdir(exist_ok=True)
    with open(HERE / "generated" / "summary.jsonl", "a") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
