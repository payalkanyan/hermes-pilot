# process-mailbox-invoices-to-draft-bills workflow (generated directly from session 'Process F09 invoices for 2026-10 #4')

Match each supplier invoice in a mailbox folder to its purchase order and delivery records, classify it, and create draft bills for the invoices that pass.

```mermaid
flowchart TD
  start(["start: mailbox_folder, period"])
  list_invoices[["<b>list_invoices</b> (tool)<br/>gets: mailbox_folder"]]
  collect_invoice_facts("<b>collect_invoice_facts</b> (agent)<br/>for each: invoices<br/>gets: item")
  classify_invoices["<b>classify_invoices</b> (code)<br/>gets: invoice_facts, period"]
  draft_gate{"<b>draft_gate</b> (branch)<br/>gets: verdicts, ok_invoices"}
  create_drafts("<b>create_drafts</b> (agent)<br/>for each: ok_invoices<br/>gets: item")
  build_result["<b>build_result</b> (code)<br/>gets: verdicts, drafts"]
  report_gaps["<b>report_gaps</b> (code)<br/>gets: verdicts"]
  report_gaps --> finish(["final answer"])
  start --> list_invoices
  list_invoices --> collect_invoice_facts
  collect_invoice_facts --> classify_invoices
  classify_invoices --> draft_gate
  draft_gate -->|all verdicts present and ok invoices exist| create_drafts
  draft_gate -->|otherwise| report_gaps
  create_drafts --> build_result
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class classify_invoices,build_result,report_gaps code;
  class collect_invoice_facts,create_drafts agent;
  class list_invoices tool;
  class draft_gate branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_invoices | tool | mailbox_folder | list_invoices | invoices | non_empty |
| collect_invoice_facts | agent | one item of `invoices` | get_invoice, get_purchase_order, get_deliveries | invoice_facts | schema, grounded_in_tool_results |
| classify_invoices | code | invoice_facts, period | - | verdicts, ok_invoices | verdict_for_every_invoice |
| draft_gate | branch | verdicts, ok_invoices | - |  | verdict_for_every_invoice |
| create_drafts | agent | one item of `ok_invoices` | create_draft_bill, get_draft_bill | drafts | schema, grounded_in_tool_results, draft_read_back_matches |
| build_result | code | verdicts, drafts | - | result | non_empty |
| report_gaps | code | verdicts | - | gap_report | non_empty |
