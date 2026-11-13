# invoice-matching-f08 workflow (generated directly from session 'Process F08 invoice matching for 2026-10')

Match one mailbox folder of supplier invoices to purchase orders for a given period, with approval gates before any file write, script run, or draft bill creation, then report matched and exception invoices.

```mermaid
flowchart TD
  start(["start: folder, period"])
  list_folder[["<b>list_folder</b> (tool)<br/>gets: folder"]]
  collect_facts("<b>collect_facts</b> (agent)<br/>for each: invoice_ids<br/>gets: item, period")
  gate_facts{"<b>gate_facts</b> (branch)<br/>gets: facts"}
  write_facts_file[["<b>write_facts_file</b> (tool)<br/>gets: facts"]]
  gate_script{"<b>gate_script</b> (branch)<br/>gets: facts_path, period"}
  write_decide_script[["<b>write_decide_script</b> (tool)<br/>gets: period"]]
  run_decide[["<b>run_decide</b> (tool)<br/>gets: script_path, facts_path, period"]]
  select_matched["<b>select_matched</b> (code)<br/>gets: verdicts, facts"]
  gate_drafts{"<b>gate_drafts</b> (branch)<br/>gets: matched"}
  create_drafts("<b>create_drafts</b> (agent)<br/>for each: matched<br/>gets: item")
  verify_drafts("<b>verify_drafts</b> (agent)<br/>for each: draft_bills<br/>gets: item")
  report_summary["<b>report_summary</b> (code)<br/>gets: verdicts, verified_drafts, facts"]
  report_summary --> finish(["final answer"])
  start --> list_folder
  list_folder --> collect_facts
  collect_facts --> gate_facts
  gate_facts -->|all collected| write_facts_file
  gate_facts -->|some missing| report_summary
  write_facts_file --> gate_script
  gate_script -->|approved| write_decide_script
  gate_script -->|rejected| report_summary
  write_decide_script --> run_decide
  run_decide --> select_matched
  select_matched --> gate_drafts
  gate_drafts -->|approved| create_drafts
  gate_drafts -->|rejected| report_summary
  create_drafts --> verify_drafts
  verify_drafts --> report_summary
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class select_matched,report_summary code;
  class collect_facts,create_drafts,verify_drafts agent;
  class list_folder,write_facts_file,write_decide_script,run_decide tool;
  class gate_facts,gate_script,gate_drafts branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_folder | tool | folder | list_invoices | invoice_ids, invoice_headers | non_empty, grounded_in_tool_results |
| collect_facts | agent | one item of `invoice_ids` + period | get_invoice, get_purchase_order, get_deliveries | facts | schema, grounded_in_tool_results, every_invoice_has_facts |
| gate_facts | branch | facts | - |  | - |
| write_facts_file | tool | facts | write_file | facts_path | non_empty, facts_file_matches_facts |
| gate_script | branch | facts_path, period | - |  | user_approves_decide_script |
| write_decide_script | tool | period | terminal | script_path | non_empty |
| run_decide | tool | script_path, facts_path, period | terminal | verdicts | non_empty, verdicts_cover_all_invoices |
| select_matched | code | verdicts, facts | - | matched | verdicts_cover_all_invoices |
| gate_drafts | branch | matched | - |  | user_approves_drafts |
| create_drafts | agent | one item of `matched` | create_draft_bill | draft_bills | schema, grounded_in_tool_results, every_matched_has_draft |
| verify_drafts | agent | one item of `draft_bills` | get_draft_bill | verified_drafts | schema, grounded_in_tool_results, draft_matches_request |
| report_summary | code | verdicts, verified_drafts, facts | - | final_report | final_report_covers_all_invoices, non_empty |
