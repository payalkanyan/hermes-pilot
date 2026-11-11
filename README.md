# Hermes workflows: a measured pilot, and a skill-to-workflow generator

Work for MnemioAI's open brief *"Workflows and evals for Hermes agents"*, built against the open-source [Hermes Agent](https://github.com/NousResearch/hermes-agent).

The brief asks one question: does splitting an agent's job into small, checked steps beat one ordinary skill? This repo answers it with numbers, and then builds the thing the answer points to.

Two parts:

1. **The pilot** — a 10-task invoice-matching suite with mock tools and a code-based grader, used to compare a plain skill against a workflow made of helper agents. Results in `REPORT.md`.
2. **The workflow layer** — a workflow spec format (a graph of nodes), a validator, a Mermaid flowchart generator, a runner that gives each node only its declared inputs, and a converter that turns an existing `SKILL.md` into a workflow spec.

**Status (November 2026):** the pilot is complete. The workflow layer runs the invoice workflow end to end on a real model; a runner that can execute *any* generated workflow is not built yet.

## Headline numbers

Model throughout: `anthropic/claude-haiku-5.5` via OpenRouter, reasoning medium. Hermes `v0.22.7` (commit `b200f5bc60e31588ba2cb60e288029c4a54ba5fa`).

**Pilot — plain skill vs helper-agent workflow**

| | Plain skill (3 runs/task) | Helper-agent workflow (1 run/task) |
|---|---|---|
| Strict success | 28/30 | 9/10 |
| First run of each task only | 10/10 | 9/10 |
| Invented ids or codes | 0/1010 | 0/187 |
| Mean cost per task, all-in | $0.0105 | $0.0482 |
| Mean API calls per task, all-in | 10.9 | 52.9 |

The workflow did not beat the plain skill, cost about 4.6x more, and hit two built-in Hermes limits on helper agents.

**Converter — the same 10 Hermes skills, four batches**

| Batch | Valid first try | Valid after one retry |
|---|---|---|
| YAML, loose rules | 7/10 | 9/10 |
| YAML, strict rules (tool names + check rules) | 5/10 | 8/10 |
| JSON, strict rules | 9/10 | 10/10 |
| JSON + no-dropping + command gate | **9/10** | **10/10** |

About $0.07 for a batch of ten. "Valid" means structurally sound, not judged for quality.

## Repo layout

### The pilot

| File | What it does |
|---|---|
| `gen_world.py` | Builds the fake data (`data/world.json`) and answer keys (`data/tasks.jsonl`). Deterministic. |
| `world_api.py` | The fake invoice system: list invoices, read one, read its order and deliveries, create and read back a draft bill. Logs every call. |
| `mock_server.py` | Exposes those six functions to Hermes as MCP tools. |
| `grade.py` | Deterministic grader: output contract, system state, invented values, step order. |
| `run_suite.py` | Runs tasks through Hermes, grades them, records tokens and cost, resumes, stops at a spend limit. |
| `helper_usage.py` | Adds up helper-agent usage from an exported session (Hermes' own usage file covers only the parent). |
| `show_failures.py` | Prints why each failed run failed. |
| `make_report.py` | Rebuilds the pilot tables. **It overwrites `REPORT.md`,** so copy that file first if you have edited it. |
| `skills/invoice-matching-baseline/` | The plain skill (the control). |
| `skills/invoice-matching-workflow/` | The helper-agent skill. Its script and schema are embedded in the text, because Hermes' terminal runs in a sandbox that cannot see your files. |
| `results/` | Raw per-run results, usage files, and per-node traces. |

### The workflow layer

| File | What it does |
|---|---|
| `workflow/invoice-matching.workflow.yaml` | The workflow as a graph of 8 nodes. Each declares its inputs, allowed tools, output schema and checks. |
| `workflow/FLOWCHART.md` | The flowchart, drawn from the spec. GitHub renders it. |
| `workflow/workflow_tools.py` | Validates a spec and draws the flowchart. |
| `workflow/workflow_runner.py` | Runs a spec node by node. Each node gets **only** its declared inputs. |
| `workflow/generate_workflow.py` | Converts a `SKILL.md` into a spec plus flowchart, validates it, retries once with the errors. |
| `workflow/checks/`, `workflow/schemas/` | The code nodes and the fact schema for the invoice workflow. |
| `workflow/generated/` | Specs and flowcharts produced from real Hermes skills, plus `summary.jsonl`. |

## The task suite (v0.2)

| Task | Invoices | Trap |
|---|---|---|
| T01 | 4 | clean, all match |
| T02 | 5 | duplicate invoice number |
| T03 | 4 | purchase order does not exist |
| T04 | 4 | 0.8% price difference allowed, 6% not |
| T05 | 4 | deliveries split over two receipts; one order under-delivered |
| T06 | 4 | totals wrong by 5.00 and by one cent |
| T07 | 4 | prompt injection hidden in an invoice note |
| T08 | 12 | every failure type, plus a wrong-month invoice that is also mispriced |
| T09 | 30 | random mix of all failure types and hidden instructions |
| T10 | 60 | same, at larger scale |

T09 and T10 were added after the plain skill passed all of T01 to T08. T01 to T08 were not changed.

## How to reproduce

You need Git, Python 3, and Hermes pinned to the version above. Use your own API key and set a spending limit with your provider first.

**1. Build the suite and self-test the grader** (no model, no cost):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install "mcp<2" pyyaml          # mcp 2.x renamed the class the server uses, so pin 1.x
python3 gen_world.py
python3 run_suite.py --condition baseline --runs 1 --oracle    # must report 10/10
```

**2. Register the fake tools** in `~/.hermes/config.yaml` (use your own absolute paths):

```yaml
mcp_servers:
  invoice_mock:
    command: "/ABS/PATH/hermes-pilot/.venv/bin/python"
    args: ["/ABS/PATH/hermes-pilot/mock_server.py"]
    timeout: 120
```

**3. Install both skills:** copy the two folders from `skills/` into `~/.hermes/skills/`.

**4. For the helper-agent condition only,** Hermes allows 2 helper agents per one-shot run by default:

```bash
hermes config set delegation.oneshot_max_children 0   # restore to 2 afterwards
```

Even then, Hermes blocks the 51st helper in one turn (`loop_subagent_cap`), which is what failed T10.

**5. Run the pilot** (keep the model fixed across every run):

```bash
export AGENT_CMD='hermes -z {prompt} --usage-file {usage} --provider openrouter -m anthropic/claude-haiku-5.5 --reasoning medium --ignore-rules'
python3 run_suite.py --condition baseline --runs 3 --max-cost 2.00
python3 run_suite.py --condition workflow --runs 1 --max-cost 3.00
python3 make_report.py
```

`--resume` continues an interrupted run, `--tasks T01,T03` runs a subset, `--tag name` writes to a separate results file.

**6. Run the graph workflow:**

```bash
python3 workflow/workflow_tools.py workflow/invoice-matching.workflow.yaml        # validate + draw
python3 workflow/workflow_runner.py workflow/invoice-matching.workflow.yaml --all --mode code    # free self-test
python3 workflow/workflow_runner.py workflow/invoice-matching.workflow.yaml --task T01 --mode hermes
```

**7. Convert skills into workflows** (about $0.07 for ten):

```bash
python3 workflow/generate_workflow.py $(find ~/projects/hermes-agent/skills -name SKILL.md | sort | awk 'NR%4==1' | head -10)
```

## The spec format

A node declares what it is, what it receives, what it may use, what it must produce, and how its output is checked:

```yaml
- id: collect_facts
  type: agent                 # agent | code | tool | branch
  for_each: invoice_ids       # runs once per item
  parallel: 10
  goal: Collect the raw facts for this one invoice.
  inputs: [item]              # ONLY these reach the node
  tools: [get_invoice, get_purchase_order, get_deliveries]
  output_schema: schemas/fact.json
  outputs: [facts]
  checks: [schema, grounded_in_tool_results]
  on_fail: {retry: 1, then: stop}
  next: [{to: decide}]
```

Rules the validator enforces:

- A node's inputs may only name a top-level input or an **earlier** node's output. `history`, `context` and `*` are rejected.
- Agent nodes need an output schema, a tool allowlist and at least one check.
- Every check must either be built in or carry a one-line rule under `check_descriptions`, so the runner can judge it.
- Tool names are compared against Hermes' own `toolsets.py`. Unknown names are warnings, since MCP tools are legitimate; a spec can declare those under `tools_provided`.
- Nothing that runs a command (`terminal`, `patch`, `write_file`, `browser_exec`, `skill_manage`) may be reached without a check on it or an approval branch directly before it.
- Branches need at least two routes, and every node must be reachable.

## Known gotchas

- **A running tool server keeps old data.** After regenerating tasks, run `pkill -f mock_server.py` so Hermes starts a fresh one. (`world_api.py` now rereads its data file, and the runner flags folder-not-found as a setup error rather than a wrong answer.)
- **Hermes' `--usage-file` excludes helper agents.** `run_suite.py` exports each workflow session and adds them back; the all-in figures include them.
- **Free model tiers rate-limit quickly.** Provider-failed runs are excluded, the runner stops on HTTP 429, and `--resume` redoes only those.
- **Tool error replies do not name the item they refer to.** This caused a real baseline failure (T03). Naming the item would probably help.
- **Ask the model for JSON, not YAML.** An unquoted colon inside a sentence broke most early conversions.
- Use Ctrl+C to stop a run, never Ctrl+Z.

## Limitations

One model and one task type. The plain skill was already near the ceiling on small tasks, so accuracy gains were hard to show. Peak context per call was never measured. The helper-agent workflow ran once per task against the plain skill's three. Generated workflows are validated but have never been executed, and "valid" does not mean faithful to the skill. Early runs on free models, and one run set broken by a stale tool server, were discarded and redone.

## Credits and licence

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research (MIT licence); Hermes itself is not copied into this repo. The brief comes from MnemioAI. Add a licence file before making this repo public.

Author: [github.com/payalkanyan](https://github.com/payalkanyan)