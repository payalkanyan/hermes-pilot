# invoice-matching-workflow workflow (generated directly from session 'Process F01 invoice matching for 2026-10 #3')

Match the supplier invoices in one mailbox folder for one period against their purchase orders and goods receipts, then create a draft bill for each clean match. Stop and report if any invoice has an exception.

```mermaid
flowchart TD
  start(["start: folder, period"])
  list_folder[["<b>list_folder</b> (tool)<br/>gets: folder"]]
  collect_facts("<b>collect_facts</b> (agent)<br/>for each: invoices<br/>gets: item")
  decide_verdicts["<b>decide_verdicts</b> (code)<br/>gets: facts, period"]
  gate_drafts{"<b>gate_drafts</b> (branch)<br/>gets: exceptions"}
  create_drafts("<b>create_drafts</b> (agent)<br/>for each: matched<br/>gets: item")
  compile_result["<b>compile_result</b> (code)<br/>gets: drafts, exceptions"]
  report_exceptions["<b>report_exceptions</b> (code)<br/>gets: exceptions"]
  report_exceptions --> finish(["final answer"])
  start --> list_folder
  list_folder --> collect_facts
  collect_facts --> decide_verdicts
  decide_verdicts --> gate_drafts
  gate_drafts -->|no exceptions| create_drafts
  gate_drafts -->|exceptions found| report_exceptions
  create_drafts --> compile_result
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class decide_verdicts,compile_result,report_exceptions code;
  class collect_facts,create_drafts agent;
  class list_folder tool;
  class gate_drafts branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_folder | tool | folder | list_invoices | invoices | non_empty, grounded_in_tool_results |
| collect_facts | agent | one item of `invoices` | get_invoice, get_purchase_order, get_deliveries | facts | schema, grounded_in_tool_results |
| decide_verdicts | code | facts, period | - | verdicts, matched, exceptions | verdicts_cover_all_invoices |
| gate_drafts | branch | exceptions | - |  | ready_for_drafts |
| create_drafts | agent | one item of `matched` | create_draft_bill, get_draft_bill | drafts | schema, grounded_in_tool_results, draft_matches_invoice |
| compile_result | code | drafts, exceptions | - | result | non_empty |
| report_exceptions | code | exceptions | - | gap_report | non_empty |
