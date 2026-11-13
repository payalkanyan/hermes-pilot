# invoice-mailbox-match-and-draft workflow (generated directly from session 'Process F02 invoice mailbox for 2026-10')

For one mailbox folder and period, collect each invoice's facts, match it against its purchase order and deliveries, and create a draft bill for each clean match.

```mermaid
flowchart TD
  start(["start: mailbox_folder, period"])
  list_invoices[["<b>list_invoices</b> (tool)<br/>gets: mailbox_folder"]]
  collect_facts("<b>collect_facts</b> (agent)<br/>for each: invoices<br/>gets: item")
  decide_verdicts["<b>decide_verdicts</b> (code)<br/>gets: facts, period"]
  approve_matches{"<b>approve_matches</b> (branch)<br/>gets: matched"}
  create_drafts("<b>create_drafts</b> (agent)<br/>for each: matched<br/>gets: item")
  build_summary["<b>build_summary</b> (code)<br/>gets: drafts, verdicts"]
  build_summary --> finish(["final answer"])
  start --> list_invoices
  list_invoices --> collect_facts
  collect_facts --> decide_verdicts
  decide_verdicts --> approve_matches
  approve_matches -->|matched invoices present| create_drafts
  approve_matches -->|no matches| build_summary
  create_drafts --> build_summary
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class decide_verdicts,build_summary code;
  class collect_facts,create_drafts agent;
  class list_invoices tool;
  class approve_matches branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_invoices | tool | mailbox_folder | list_invoices | invoices | non_empty |
| collect_facts | agent | one item of `invoices` | get_invoice, get_purchase_order, get_deliveries | facts | schema, grounded_in_tool_results |
| decide_verdicts | code | facts, period | - | verdicts, matched | non_empty, verdict_rules_applied, every_invoice_has_verdict |
| approve_matches | branch | matched | - |  | - |
| create_drafts | agent | one item of `matched` | create_draft_bill, get_draft_bill | drafts | schema, grounded_in_tool_results, draft_readback_matches |
| build_summary | code | drafts, verdicts | - | result | non_empty, every_invoice_accounted_for |
