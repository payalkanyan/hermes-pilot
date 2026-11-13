# invoice-matching-workflow workflow (generated directly from session 'Process F04 invoices for 2026-10 #3')

Match each supplier invoice in a mailbox folder for a given month to its purchase order and delivery records, decide ok or exception per invoice, and create draft bills for the matched ones after user approval.

```mermaid
flowchart TD
  start(["start: folder, period"])
  list_invoices[["<b>list_invoices</b> (tool)<br/>gets: folder"]]
  collect_invoice_facts("<b>collect_invoice_facts</b> (agent)<br/>for each: invoice_ids<br/>gets: item")
  gate_write_facts{"<b>gate_write_facts</b> (branch)<br/>gets: invoice_facts"}
  write_and_run_decision["<b>write_and_run_decision</b> (code)<br/>gets: invoice_facts, period"]
  gate_draft_bills{"<b>gate_draft_bills</b> (branch)<br/>gets: matched_invoices, exceptions"}
  create_draft_bills("<b>create_draft_bills</b> (agent)<br/>for each: matched_invoices<br/>gets: item")
  compile_report["<b>compile_report</b> (code)<br/>gets: matched_invoices, exceptions, draft_bills"]
  compile_report --> finish(["final answer"])
  start --> list_invoices
  list_invoices --> collect_invoice_facts
  collect_invoice_facts --> gate_write_facts
  gate_write_facts -->|approved| write_and_run_decision
  gate_write_facts -->|rejected| compile_report
  write_and_run_decision --> gate_draft_bills
  gate_draft_bills -->|approved| create_draft_bills
  gate_draft_bills -->|rejected| compile_report
  create_draft_bills --> compile_report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class write_and_run_decision,compile_report code;
  class collect_invoice_facts,create_draft_bills agent;
  class list_invoices tool;
  class gate_write_facts,gate_draft_bills branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_invoices | tool | folder | list_invoices | invoice_ids | non_empty, environment_probe_ok |
| collect_invoice_facts | agent | one item of `invoice_ids` | get_invoice, get_purchase_order, get_deliveries | invoice_facts | schema, grounded_in_tool_results |
| gate_write_facts | branch | invoice_facts | - |  | user_approval_recorded |
| write_and_run_decision | code | invoice_facts, period | - | verdicts, matched_invoices, exceptions | one_verdict_per_invoice |
| gate_draft_bills | branch | matched_invoices, exceptions | - |  | user_approval_recorded |
| create_draft_bills | agent | one item of `matched_invoices` | create_draft_bill, get_draft_bill | draft_bills | schema, grounded_in_tool_results, draft_matches_invoice |
| compile_report | code | matched_invoices, exceptions, draft_bills | - | final_result | every_invoice_accounted_for |
