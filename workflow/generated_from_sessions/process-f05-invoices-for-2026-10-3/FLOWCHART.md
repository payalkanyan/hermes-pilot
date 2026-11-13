# process-mailbox-invoices-for-month workflow (generated directly from session 'Process F05 invoices for 2026-10 #3')

Match each supplier invoice in a mailbox folder to its purchase order and deliveries for a given month, reject invoices that fail the rules, and create draft bills for the ones that pass.

```mermaid
flowchart TD
  start(["start: folder, month"])
  list_folder[["<b>list_folder</b> (tool)<br/>gets: folder"]]
  fetch_invoice[["<b>fetch_invoice</b> (tool)<br/>for each: invoices<br/>gets: item"]]
  fetch_purchase_order[["<b>fetch_purchase_order</b> (tool)<br/>for each: invoice_details<br/>gets: item"]]
  fetch_deliveries[["<b>fetch_deliveries</b> (tool)<br/>for each: invoice_details<br/>gets: item"]]
  build_facts["<b>build_facts</b> (code)<br/>gets: invoice_details, purchase_orders, deliveries"]
  gate_before_script{"<b>gate_before_script</b> (branch)<br/>gets: facts, month"}
  compose_decision_script("<b>compose_decision_script</b> (agent)<br/>gets: month")
  run_decision[["<b>run_decision</b> (tool)<br/>gets: script_path, facts, month"]]
  gate_before_drafts{"<b>gate_before_drafts</b> (branch)<br/>gets: ok_invoices, exceptions"}
  create_draft_bills("<b>create_draft_bills</b> (agent)<br/>for each: ok_invoices<br/>gets: item")
  report_summary["<b>report_summary</b> (code)<br/>gets: drafts, exceptions"]
  report_stopped["<b>report_stopped</b> (code)<br/>gets: facts"]
  report_stopped --> finish(["final answer"])
  start --> list_folder
  list_folder --> fetch_invoice
  fetch_invoice --> fetch_purchase_order
  fetch_purchase_order --> fetch_deliveries
  fetch_deliveries --> build_facts
  build_facts --> gate_before_script
  gate_before_script -->|approved| compose_decision_script
  gate_before_script -->|not approved| report_stopped
  compose_decision_script --> run_decision
  run_decision --> gate_before_drafts
  gate_before_drafts -->|approved| create_draft_bills
  gate_before_drafts -->|not approved| report_stopped
  create_draft_bills --> report_summary
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class build_facts,report_summary,report_stopped code;
  class compose_decision_script,create_draft_bills agent;
  class list_folder,fetch_invoice,fetch_purchase_order,fetch_deliveries,run_decision tool;
  class gate_before_script,gate_before_drafts branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_folder | tool | folder | list_invoices | invoices | non_empty |
| fetch_invoice | tool | one item of `invoices` | get_invoice | invoice_details | non_empty |
| fetch_purchase_order | tool | one item of `invoice_details` | get_purchase_order | purchase_orders | non_empty |
| fetch_deliveries | tool | one item of `invoice_details` | get_deliveries | deliveries | non_empty |
| build_facts | code | invoice_details, purchase_orders, deliveries | - | facts | every_invoice_has_facts |
| gate_before_script | branch | facts, month | - |  | user_approves_run |
| compose_decision_script | agent | month | write_file | script_path | schema, non_empty, script_implements_rules |
| run_decision | tool | script_path, facts, month | terminal | ok_invoices, exceptions | verdicts_cover_all_invoices |
| gate_before_drafts | branch | ok_invoices, exceptions | - |  | user_approves_drafts |
| create_draft_bills | agent | one item of `ok_invoices` | create_draft_bill, get_draft_bill | drafts | schema, grounded_in_tool_results |
| report_summary | code | drafts, exceptions | - | summary | every_invoice_accounted_for |
| report_stopped | code | facts | - | stop_message | non_empty |
