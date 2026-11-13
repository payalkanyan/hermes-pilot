# process-invoice-mailbox-folder workflow (generated directly from session 'Process F03 invoice mailbox for 2026-10')

List the invoices in one mailbox folder, collect each invoice's purchase order and deliveries, classify them for a period, create draft bills for the clean matches after approval, and report matches and exceptions.

```mermaid
flowchart TD
  start(["start: mailbox_folder, period"])
  list_invoices[["<b>list_invoices</b> (tool)<br/>gets: mailbox_folder"]]
  collect_invoice_facts("<b>collect_invoice_facts</b> (agent)<br/>for each: invoices<br/>gets: item")
  gate_decision_script{"<b>gate_decision_script</b> (branch)<br/>gets: invoice_facts"}
  decide_verdicts["<b>decide_verdicts</b> (code)<br/>gets: invoice_facts, period"]
  gate_drafts{"<b>gate_drafts</b> (branch)<br/>gets: bill_requests"}
  create_draft_bills("<b>create_draft_bills</b> (agent)<br/>for each: bill_requests<br/>gets: item")
  compile_report["<b>compile_report</b> (code)<br/>gets: verdicts, drafts"]
  compile_report --> finish(["final answer"])
  start --> list_invoices
  list_invoices --> collect_invoice_facts
  collect_invoice_facts --> gate_decision_script
  gate_decision_script -->|approved| decide_verdicts
  gate_decision_script -->|not approved| compile_report
  decide_verdicts --> gate_drafts
  gate_drafts -->|approved| create_draft_bills
  gate_drafts -->|not approved| compile_report
  create_draft_bills --> compile_report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class gate_decision_script,gate_drafts branch;
  class collect_invoice_facts,create_draft_bills agent;
  class list_invoices tool;
  class decide_verdicts,compile_report code;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_invoices | tool | mailbox_folder | list_invoices | invoices | non_empty, grounded_in_tool_results |
| collect_invoice_facts | agent | one item of `invoices` | get_invoice, get_purchase_order, get_deliveries | invoice_facts | schema, grounded_in_tool_results |
| gate_decision_script | branch | invoice_facts | - |  | user_approves_step |
| decide_verdicts | code | invoice_facts, period | - | verdicts, bill_requests | verdicts_cover_every_invoice |
| gate_drafts | branch | bill_requests | - |  | user_approves_step |
| create_draft_bills | agent | one item of `bill_requests` | create_draft_bill, get_draft_bill | drafts | schema, grounded_in_tool_results, draft_read_back_matches |
| compile_report | code | verdicts, drafts | - | final_summary | non_empty |
