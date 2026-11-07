# Hermes pilot: plain skills vs a checked workflow

A small, reproducible experiment for MnemioAI's open brief "Workflows and evals for Hermes agents". It asks one question: does splitting a job into small steps (one helper agent per item, code-checked rules, read-back before writing) beat one ordinary skill on the open-source [Hermes Agent](https://github.com/NousResearch/hermes-agent)?

The test job is **monthly supplier-invoice matching** against fake purchase orders and deliveries. Every answer is graded by code against a prewritten answer key. No AI judge is used, and nothing touches a real system.

**Status:** pilot complete (November 2026). Results are a first look, not proof: one model, one task type, a small suite. See `REPORT.md` for the full write-up and caveats.

## Headline results

Model: `anthropic/claude-haiku-5.5` via OpenRouter, reasoning medium. Hermes `v0.22.7` (commit `b200f5bc60e31588ba2cb60e288029c4a54ba5fa`).

| Measure | Plain skill (3 runs per task) | Workflow (1 run per task) |
|---|---|---|
| Strict success | 28/30 | 9/10 |
| First run of each task only (fair comparison) | 10/10 | 9/10 |
| Invented ids or codes | 0/1010 | 0/187 |
| Mean cost per task, all-in | $0.0105 | $0.0482 |
| Mean API calls per task, all-in | 10.9 | 52.9 |
| Median seconds per task | 24.6 | 42.0 |

In short: the workflow did not beat the plain skill overall, cost about 4.6x more, and hit two built-in Hermes limits on helper agents at 60 invoices. See `REPORT.md` for findings and the recommended next step.

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

## What is in this repo

| File | What it does |
|---|---|
| `gen_world.py` | Builds the fake data (`data/world.json`) and answer keys (`data/tasks.jsonl`). Deterministic. |
| `world_api.py` | The fake invoice system: list invoices, read an invoice, order and deliveries, create and read back a draft bill. Logs every call. |
| `mock_server.py` | Exposes those functions to Hermes as MCP tools. |
| `grade.py` | Deterministic grader: output contract, system state, invented values, step order. |
| `run_suite.py` | Runs tasks through Hermes, grades them, records tokens and cost, resumes, stops at a spend limit. |
| `helper_usage.py` | Adds up helper-agent usage from an exported Hermes session (Hermes' own usage file covers only the parent agent). |
| `show_failures.py` | Prints why each failed run failed. |
| `make_report.py` | Builds `REPORT.md` from the results files. |
| `skills/invoice-matching-baseline/` | The plain skill (the control). |
| `skills/invoice-matching-workflow/` | The workflow skill (the script and schema are embedded, because Hermes' terminal runs in a sandbox that cannot see your files). |
| `results/` | Raw per-run results and usage files. |

## How to reproduce

You need Git, Python 3, and Hermes installed and pinned to the version above. Use your own API key and set a spending limit with your provider first.

1. **Build the suite and self-test the grader** (uses no model and costs nothing):
   ```
   python3 -m venv .venv && source .venv/bin/activate
   pip install "mcp<2"
   python3 gen_world.py
   python3 run_suite.py --condition baseline --runs 1 --oracle
   ```
   The last command must report 10/10. (`mcp` 2.x renamed the class the server uses, so pin 1.x.)

2. **Register the fake tools** by adding this to `~/.hermes/config.yaml` (use your own absolute paths):
   ```yaml
   mcp_servers:
     invoice_mock:
       command: "/ABS/PATH/hermes-pilot/.venv/bin/python"
       args: ["/ABS/PATH/hermes-pilot/mock_server.py"]
       timeout: 120
   ```

3. **Install both skills:** copy the two folders from `skills/` into `~/.hermes/skills/`.

4. **For the workflow condition only,** Hermes' one-shot mode allows 2 helper agents per run by default. The experiment raised this for the pilot:
   ```
   hermes config set delegation.oneshot_max_children 0
   ```
   Restore it afterwards with `... 2`. Even then, Hermes blocks the 51st helper in one turn (`loop_subagent_cap`), which is what failed T10.

5. **Run** (replace the model values with yours; keep them fixed for every run):
   ```
   export AGENT_CMD='hermes -z {prompt} --usage-file {usage} --provider openrouter -m anthropic/claude-haiku-5.5 --reasoning medium --ignore-rules'
   python3 run_suite.py --condition baseline --runs 3 --max-cost 2.00
   python3 run_suite.py --condition workflow --runs 1 --max-cost 3.00
   python3 make_report.py
   ```
   `--resume` continues an interrupted run, `--tasks T01,T03` runs a subset, and `--tag name` writes to a separate results file.

## Metrics

- **Strict success:** the final JSON matches the contract exactly (each reason is a bare code), the right draft bills exist in the fake system, and none exist for invoices that should be rejected.
- **Semantic success:** the same, but ignores extra words in the reason text.
- **Invented values:** reported ids or codes that do not exist in the data.
- **Step adherence:** before each draft, the agent read the invoice, its order and its deliveries, and read the draft back.
- **All-in cost and calls:** parent agent plus helper agents.

## Known gotchas

- A running tool server keeps old data. If you regenerate the tasks, stop it so Hermes starts a fresh one: `pkill -f mock_server.py`. (`world_api.py` now rereads the data file, and the runner flags "folder not found" as a setup error instead of a wrong answer.)
- Hermes' `--usage-file` excludes helper agents. `run_suite.py` exports each workflow session and adds the helpers back.
- Free model tiers rate-limit quickly. The runner marks provider-failed runs as excluded, stops on HTTP 429, and `--resume` redoes only those.
- Tool error replies do not name the item they refer to. This caused a real baseline failure (T03). Naming it would probably help.
- Use Ctrl+C to stop a run, not Ctrl+Z.

## Limitations

One model (Haiku 5.5) and one task type. The plain skill was already near the ceiling on small tasks, so accuracy gains were hard to show. Peak context per call was not measured. The workflow ran once per task; the plain skill three times. Early runs on free models and one run set broken by a stale tool server were discarded and redone.

## Credits and licence

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research (MIT licence). Hermes itself is not copied into this repo. The brief comes from MnemioAI. Add a licence file of your choice before making this repo public.
