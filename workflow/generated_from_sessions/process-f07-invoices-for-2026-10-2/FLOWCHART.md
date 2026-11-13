# process-invoices-for-folder workflow (generated directly from session 'Process F07 invoices for 2026-10 #2')

Match one mailbox folder of supplier invoices to purchase orders for a given month, create draft bills only for clean matches, and report exceptions.

```mermaid
flowchart TD
  start(["start: folder, period"])
  list_folder[["<b>list_folder</b> (tool)<br/>gets: folder, period"]]
  fetch_facts("<b>fetch_facts</b> (agent)<br/>for each: invoice_refs<br/>gets: item")
  gate_facts{"<b>gate_facts</b> (branch)<br/>gets: facts"}
  decide_verdicts["<b>decide_verdicts</b> (code)<br/>gets: facts, period"]
  gate_drafts{"<b>gate_drafts</b> (branch)<br/>gets: verdicts, facts"}
  create_drafts("<b>create_drafts</b> (agent)<br/>for each: verdicts<br/>gets: item")
  compile_report["<b>compile_report</b> (code)<br/>gets: drafts, verdicts"]
  report_gaps["<b>report_gaps</b> (code)<br/>gets: facts"]
  report_gaps --> finish(["final answer"])
  start --> list_folder
  list_folder --> fetch_facts
  fetch_facts --> gate_facts
  gate_facts -->|all facts gathered| decide_verdicts
  gate_facts -->|some facts missing| report_gaps
  decide_verdicts --> gate_drafts
  gate_drafts -->|some ok| create_drafts
  gate_drafts -->|none ok| compile_report
  create_drafts --> compile_report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class decide_verdicts,compile_report,report_gaps code;
  class fetch_facts,create_drafts agent;
  class list_folder tool;
  class gate_facts,gate_drafts branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_folder | tool | folder, period | list_invoices | invoice_refs | non_empty |
| fetch_facts | agent | one item of `invoice_refs` | get_invoice, get_purchase_order, get_deliveries | facts | schema, grounded_in_tool_results, facts_complete |
| gate_facts | branch | facts | - |  | facts_complete |
| decide_verdicts | code | facts, period | - | verdicts | verdict_per_invoice |
| gate_drafts | branch | verdicts, facts | - |  | verdict_per_invoice, no_embedded_instruction_followed |
| create_drafts | agent | one item of `verdicts` | create_draft_bill, get_draft_bill | drafts | schema, grounded_in_tool_results |
| compile_report | code | drafts, verdicts | - | result | all_invoices_accounted, non_empty |
| report_gaps | code | facts | - | gap_report | non_empty |
