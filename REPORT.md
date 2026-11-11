# Workflows and evals for Hermes agents: pilot results and a skill-to-workflow generator

Prepared for MnemioAI against the open brief *"Workflows and evals for Hermes agents"*, November 2026.

Everything below is a first look, not proof: one model, one task type, few runs per condition. Raw results are in `results/` and `workflow/generated/summary.jsonl`.

**Setup used throughout:** Hermes Agent `v0.22.7` (commit `b200f5bc60e3`), model `anthropic/claude-haiku-5.5` via OpenRouter, reasoning medium, mock MCP tools, a deterministic grader with no model judge.

---

## 1. What was asked, and what came back

The brief's hypothesis: if a task is split into steps that each have one goal, see only their declared inputs, return structured output and must pass a check, the agent will use less context, invent fewer facts and finish more tasks correctly.

On this suite, **that did not hold for accuracy**. A plain Hermes skill on a capable model was already close to the ceiling, and the step-by-step version cost several times more. What the structure did buy was a guaranteed output contract, arithmetic done in code rather than by the model, and per-step traces.

The second half of the work answers a follow-up from Mnemio: Hermes writes a skill after a successful task, so a workflow should be generated the same way, as a graph of nodes rather than prose, with each node receiving only the context it needs. That generator now exists and converts 9 of 10 real Hermes skills into valid specs on the first attempt.

---

## 2. The test suite

Monthly supplier-invoice matching, chosen because every correct answer can be derived in code. Six rules: in-period date, not a duplicate, lines plus tax equal the total to the cent, the purchase order exists, prices within 1% of the order, and quantity not exceeding what was delivered. A passing invoice gets a draft bill; a failing one gets no draft and a single reason code.

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

T09 and T10 were added **after** the plain skill passed all of T01 to T08; T01 to T08 were unchanged.

Grading is entirely deterministic: the final JSON against the answer key, the draft bills actually present in the mock system, whether any reported id was invented, and whether each draft was preceded by reading the invoice, its order and its deliveries and followed by a read-back.

---

## 3. Pilot results: plain skill vs helper-agent workflow

| Measure | Plain skill | Helper-agent workflow |
|---|---|---|
| Scored runs | 30 (10 tasks x 3) | 10 (10 tasks x 1) |
| Strict success (exact output contract) | 28/30 | 9/10 |
| Semantic success (right invoices, reasons, drafts) | 29/30 | 9/10 |
| Strict success, first run of each task only | 10/10 | 9/10 |
| System ended in the right state | 29/30 | 9/10 |
| Invented ids or codes | 0/1010 | 0/187 |
| Reason-text format slips | 13 | 0 |
| Mean step adherence | 0.99 | 0.90 |
| Mean cost per task, all-in | $0.0105 | $0.0482 |
| Mean API calls per task, all-in | 10.9 | 52.9 |
| Median seconds per task | 24.6 | 42.0 |

All-in cost and calls include helper agents, read back from exported sessions, because Hermes' own `--usage-file` reports only the parent agent.

Per task:

| Task | Plain skill | Helper-agent workflow |
|---|---|---|
| T01, T02, T04 to T08 | 3/3 each | 1/1 each |
| T03 | 2/3 (and 4/6 in a follow-up batch) | 1/1 |
| T09 | 2/3 | 1/1 |
| T10 | 3/3 | **0/1** |

**In one line:** the workflow scored 9/10 against 10/10 first runs for the plain skill, at roughly 4.6x the cost and 4.9x the API calls, and it failed the largest task.

---

## 4. A third option: an external node runner

A separate runner executes the same job as a graph of 8 nodes, with each AI node in its own fresh Hermes session receiving only its declared inputs, and the rule checks as plain code.

| | Plain skill | Helper agents | Node runner |
|---|---|---|---|
| T01 result | pass | pass | pass |
| T01 cost | ~$0.005 | ~$0.030 | ~$0.014 |
| T01 time | ~25s | 51s | 9.5s |
| T01 model calls | ~10 | ~24 | 20 |

One run each, so treat as indicative. The runner is faster because independent nodes run side by side, and cheaper than helper agents because fewer sessions carry Hermes' full instruction overhead. It passes all 10 tasks in a free self-test mode with a stand-in agent, but has only been run against a real model on T01.

---

## 5. Findings from reading the transcripts

1. **A plain skill mismatched a tool error to the wrong item (T03).** On the task with one missing purchase order, the agent sometimes rejected a clean invoice as `quantity_exceeds_delivery`. The exported session shows why: it sent all lookups in parallel, received a "no deliveries found" error that **does not name the purchase order it refers to**, and attached it to the wrong invoice. The data was correct. Naming the item in error replies would likely remove this failure class.
2. **Model arithmetic is unreliable on long tasks, even when the verdict is right (T09).** In one 30-invoice run, every classification was correct, but the sums shown were wrong (it wrote lines of 1,177.50 where the true subtotal was 652.50) and every reason carried an explanation that broke the output contract. This is the clearest argument for computing in code.
3. **Hermes already defends against prompt injection.** Every tool result is wrapped in a notice telling the model to treat it as data, not instructions. The injection traps (T07, and hidden notes in T09 and T10) were never followed, on either condition.
4. **Two helper-agent caps constrain the subagent design.** `delegation.oneshot_max_children` defaults to **2** per one-shot run, so an unmodified Hermes refuses the helpers and the agent quietly does the work itself. With that raised, a separate `loop_subagent_cap` guardrail blocks the **51st** helper in a turn, which is what failed T10 at 60 invoices. One helper per item therefore does not scale without either a config change, batching several items per helper, or an external runner.
5. **The usage report undercounts subagent work.** `--usage-file` covers the parent only. On one task the helpers made 15 API calls while the report said 8. Any cost comparison involving subagents must add them back.

---

## 6. The workflow spec, flowchart and context rule

A workflow is a graph of nodes of four kinds: `agent` (an AI step), `code` (a script), `tool` (one direct call) and `branch` (a split). Each node declares `inputs`, `outputs`, `tools`, `output_schema`, `checks` and `next`. A flowchart is drawn from the spec, so the diagram can never drift from what runs.

The context rule is enforced, not merely requested: a node may only name a top-level input or an **earlier** node's output, and the runner passes nothing else. `history`, `context` and `*` are rejected outright. In the invoice workflow, the fact-collection node receives one invoice id and nothing more.

The validator also requires: a schema, a tool allowlist and a check on every agent node; a written rule for any check that is not built in, so a judge can run it; tool names compared against Hermes' own `toolsets.py` (unknown names are warnings, since MCP tools are legitimate and can be declared); at least two routes on a branch; every node reachable; and **no node that runs a command** (`terminal`, `patch`, `write_file`, `browser_exec`, `skill_manage`) reachable without a check on it or an approval branch directly before it.

---

## 7. Generator results: SKILL.md to workflow spec

The converter sends one skill to the model, validates the reply, and sends the errors back once. Measured on the same 10 Hermes skills, chosen as every fourth skill in the repo to avoid cherry-picking.

| Batch | Change | Valid first try | Valid after one retry |
|---|---|---|---|
| 1 | YAML output, loose rules | 7/10 | 9/10 |
| 2 | + tool-name checking, + rules required for custom checks | 5/10 | 8/10 |
| 3 | + JSON output instead of YAML | 9/10 | 10/10 |
| 4 | + no-dropping rule, + command gate | **9/10** | **10/10** |

About $0.07 per batch of ten, roughly 0.7 cents per skill.

Three results worth acting on:

- **Most early failures were serialization, not reasoning.** Goals like `"Assemble the final answer: the verified output"` broke YAML on an unquoted colon. Asking for JSON and saving it as YAML took first-try validity from 5/10 to 9/10. Ask models for JSON.
- **A "do not drop steps" rule restored lost detail without costing validity.** Batch 3 produced noticeably thinner graphs (maps 4 nodes, humanizer 5). Batch 4 brought them back (maps 7, humanizer 11) at the same 9/10.
- **Not every skill is workflow-shaped.** The `humanizer` skill converted faithfully: its six numbered steps became nodes, and its quality requirements ("preserve meaning", "maintain voice", "add soul") became named checks. The `maps` skill is a command catalogue, and it collapsed into classify, route, run, report, losing the multi-step examples. Procedural skills convert; reference skills do not. This is a useful boundary for where the feature should apply.

The generator output is also **non-deterministic**: the same skill produced different graphs and different node counts across batches, and individual skills flipped between valid and invalid. A generated workflow is a draft for review, not a finished artifact, which supports saving it as a draft until a person approves it.

---

## 8. Caveats

- One model only (Claude Haiku 5.5 through OpenRouter, reasoning medium). Results may differ on weaker or stronger models; the brief's own E8 asks about exactly that.
- Suite v0.1 (8 tasks) was passed fully by the plain skill, so two larger tasks were added afterwards as v0.2.
- Plain skill: 3 runs per task. Helper-agent workflow: 1 run per task. Compare rates and the first-run row; `pass^k` is not comparable across different run counts.
- The helper-agent runs required `delegation.oneshot_max_children` raised to 0 in the Hermes config. The plain skill uses no helpers. This is a safety limit and should be restored after measuring.
- Strict success requires the exact output contract (a bare reason code). Semantic success ignores extra words. One 30-invoice run's 13 "invented field" counts were reclassified as reason-text format slips once the grader separated the two.
- Early runs on free models were discarded (rate limits, one model retired mid-project). One run set was invalidated by a stale mock-tool server holding old data; those runs were deleted and redone.
- For the generator, **valid means structurally sound, not faithful**. Only two generated workflows were read against their source skills by hand.
- No generated workflow has ever been executed. The node runner currently executes only the hand-written invoice workflow.
- Peak context per call, one of the brief's target metrics, was not measured. Per-node input sizes are recorded in the traces, which is a partial substitute.

---

## 9. Recommendation

**Do not build Option A (one helper agent per item) as it stands.** On a capable model it bought no accuracy on this suite, cost about 4.6x more, and ran into two Hermes caps, one of which failed the 60-invoice task outright.

**The parts worth keeping are the cheap ones:** a declared output contract per step, rule checks and arithmetic in code rather than in the model, and a read-back against the system of record before reporting success. Those are what fixed the two real plain-skill failures, and they cost almost nothing.

**Build next, in this order:**

1. A runner that can execute any valid generated workflow, not just the invoice one. This is the gap between a spec that validates and a workflow that works, and it is where Option B earns its keep.
2. The automatic trigger: generate a draft workflow after a successful task, store it beside the skill, never replacing it, and leave it as a draft until a person approves it.
3. A rerun of the whole comparison on a cheaper, weaker model, where a plain skill should fail more often and the structure has room to show value. This is the single experiment most likely to change the conclusion above.

**Suggested defaults for the open design questions:** a task counts as successful when it finishes with no tool errors and passes its own checks; each AI node runs in a fresh session, since that is what makes the context rule real (about a third of a cent of fixed overhead per node on Haiku); and the workflow sits beside the skill rather than replacing it.