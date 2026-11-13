# process-invoice-mailbox-folder workflow (generated directly from session 'Process invoice mailbox folder F10 2026-10')

Match one mailbox folder of supplier invoices for a given period against purchase orders and deliveries, then produce a verdict per invoice and a summary report.

```mermaid
flowchart TD
  start(["start: folder, period"])
  list_folder_invoices[["<b>list_folder_invoices</b> (tool)<br/>gets: folder"]]
  fetch_invoice_facts("<b>fetch_invoice_facts</b> (agent)<br/>for each: invoices<br/>gets: item")
  facts_gate{"<b>facts_gate</b> (branch)<br/>gets: facts"}
  approve_script_write{"<b>approve_script_write</b> (branch)<br/>gets: facts"}
  write_decide_script[["<b>write_decide_script</b> (tool)<br/>gets: period"]]
  decide_verdicts["<b>decide_verdicts</b> (code)<br/>gets: facts, period, script_path"]
  report_gaps["<b>report_gaps</b> (code)<br/>gets: facts"]
  build_report["<b>build_report</b> (code)<br/>gets: verdicts"]
  build_report --> finish(["final answer"])
  start --> list_folder_invoices
  list_folder_invoices --> fetch_invoice_facts
  fetch_invoice_facts --> facts_gate
  facts_gate -->|all facts collected| approve_script_write
  facts_gate -->|some missing| report_gaps
  approve_script_write -->|approved| write_decide_script
  approve_script_write -->|declined| report_gaps
  write_decide_script --> decide_verdicts
  decide_verdicts --> build_report
  report_gaps --> build_report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class decide_verdicts,report_gaps,build_report code;
  class fetch_invoice_facts agent;
  class list_folder_invoices,write_decide_script tool;
  class facts_gate,approve_script_write branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_folder_invoices | tool | folder | list_invoices | invoices | non_empty |
| fetch_invoice_facts | agent | one item of `invoices` | get_invoice, get_purchase_order, get_deliveries | facts | schema, grounded_in_tool_results, no_invented_values |
| facts_gate | branch | facts | - |  | all_items_collected |
| approve_script_write | branch | facts | - |  | user_approves_write |
| write_decide_script | tool | period | write_file | script_path | non_empty |
| decide_verdicts | code | facts, period, script_path | - | verdicts | verdict_per_invoice |
| report_gaps | code | facts | - | gap_report | non_empty |
| build_report | code | verdicts | - | report | report_has_all_verdicts |
