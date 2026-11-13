# process-mailbox-invoices-to-draft-bills workflow (generated directly from session 'Process F06 invoices for 2026-10 #4')

For one mailbox folder and period, check each supplier invoice against its purchase order and deliveries, create draft bills for invoices that pass, and report matches and exceptions.

```mermaid
flowchart TD
  start(["start: mailbox_folder, period"])
  list_folder[["<b>list_folder</b> (tool)<br/>gets: mailbox_folder"]]
  collect_facts("<b>collect_facts</b> (agent)<br/>for each: invoices<br/>gets: item")
  decide["<b>decide</b> (code)<br/>gets: facts, period"]
  gate_drafts{"<b>gate_drafts</b> (branch)<br/>gets: matched"}
  create_drafts("<b>create_drafts</b> (agent)<br/>for each: matched<br/>gets: item")
  build_report["<b>build_report</b> (code)<br/>gets: drafts, exceptions"]
  build_report --> finish(["final answer"])
  start --> list_folder
  list_folder --> collect_facts
  collect_facts --> decide
  decide --> gate_drafts
  gate_drafts -->|ok invoices present| create_drafts
  gate_drafts -->|no ok invoices| build_report
  create_drafts --> build_report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class decide,build_report code;
  class collect_facts,create_drafts agent;
  class list_folder tool;
  class gate_drafts branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_folder | tool | mailbox_folder | list_invoices | invoices | non_empty |
| collect_facts | agent | one item of `invoices` | get_invoice, get_purchase_order, get_deliveries | facts | schema, grounded_in_tool_results |
| decide | code | facts, period | - | verdicts, matched, exceptions | verdicts_cover_all_invoices, every_invoice_accounted_for |
| gate_drafts | branch | matched | - |  | ok_only_matches, ok_invoices_present |
| create_drafts | agent | one item of `matched` | create_draft_bill, get_draft_bill | drafts | schema, grounded_in_tool_results, drafts_match_matched |
| build_report | code | drafts, exceptions | - | final_report | non_empty, every_invoice_accounted_for |
