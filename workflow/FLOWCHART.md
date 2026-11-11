# invoice-matching workflow

Match one folder of supplier invoices to purchase orders and deliveries, create draft bills for the ones that pass, and report the rest.

**Context rule:** fresh context per node; only the declared inputs are passed.

Legend: rounded = AI agent node, double-bordered = tool call, square = code, diamond = branch.

```mermaid
flowchart TD
  start(["start: folder, month"])
  list_invoices[["<b>list_invoices</b> (tool)<br/>gets: folder"]]
  collect_facts("<b>collect_facts</b> (agent)<br/>for each: invoice_ids<br/>gets: item")
  decide["<b>decide</b> (code)<br/>gets: facts, month"]
  route{"<b>route</b> (branch)<br/>gets: verdicts, facts"}
  create_draft[["<b>create_draft</b> (tool)<br/>for each: ok_items<br/>gets: item"]]
  read_back[["<b>read_back</b> (tool)<br/>for each: drafts<br/>gets: item"]]
  record_exceptions["<b>record_exceptions</b> (code)<br/>gets: exception_items"]
  report["<b>report</b> (code)<br/>gets: confirmed_drafts, exceptions"]
  report --> finish(["final answer"])
  start --> list_invoices
  list_invoices --> collect_facts
  collect_facts --> decide
  decide --> route
  route -->|verdict is ok| create_draft
  route -->|any other verdict| record_exceptions
  create_draft --> read_back
  read_back --> report
  record_exceptions --> report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class collect_facts agent;
  class decide,record_exceptions,report code;
  class route branch;
  class list_invoices,create_draft,read_back tool;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| list_invoices | tool | folder | list_invoices | invoice_ids | schema, non_empty |
| collect_facts | agent | one item of `invoice_ids` | get_invoice, get_purchase_order, get_deliveries | facts | schema, grounded_in_tool_results |
| decide | code | facts, month | - | verdicts | schema, one_verdict_per_invoice |
| route | branch | verdicts, facts | - | ok_items, exception_items | - |
| create_draft | tool | one item of `ok_items` | create_draft_bill | drafts | schema |
| read_back | tool | one item of `drafts` | get_draft_bill | confirmed_drafts | readback_matches_total |
| record_exceptions | code | exception_items | - | exceptions | schema |
| report | code | confirmed_drafts, exceptions | - | final_answer | schema, reasons_are_bare_codes |
