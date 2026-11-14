# collect-invoice-raw-facts workflow (generated directly from session 'Collect invoice T01-INV-04 raw facts')

Collect the raw facts for one invoice (invoice header, lines, tax, total) and its purchase order and delivery receipt lines, copied exactly as the invoice tools return them.

```mermaid
flowchart TD
  start(["start: invoice_id"])
  get_invoice[["<b>get_invoice</b> (tool)<br/>gets: invoice_id"]]
  read_po_ref["<b>read_po_ref</b> (code)<br/>gets: invoice"]
  get_purchase_order[["<b>get_purchase_order</b> (tool)<br/>gets: po_ref"]]
  get_deliveries[["<b>get_deliveries</b> (tool)<br/>gets: po_ref"]]
  assemble_facts["<b>assemble_facts</b> (code)<br/>gets: invoice, purchase_order, deliveries"]
  assemble_facts --> finish(["final answer"])
  start --> get_invoice
  get_invoice --> read_po_ref
  read_po_ref --> get_purchase_order
  get_purchase_order --> get_deliveries
  get_deliveries --> assemble_facts
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class get_invoice,get_purchase_order,get_deliveries tool;
  class read_po_ref,assemble_facts code;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| get_invoice | tool | invoice_id | get_invoice | invoice | non_empty |
| read_po_ref | code | invoice | - | po_ref | non_empty |
| get_purchase_order | tool | po_ref | get_purchase_order | purchase_order | non_empty |
| get_deliveries | tool | po_ref | get_deliveries | deliveries | non_empty |
| assemble_facts | code | invoice, purchase_order, deliveries | - | facts | non_empty, po_not_found_handled, grounded_in_tool_results |
