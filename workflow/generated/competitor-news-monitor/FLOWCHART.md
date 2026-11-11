# competitor-news-monitor workflow (generated from the competitor-news-monitor skill)

Each tick, collect new primary-sourced news for a declared competitor watchlist, dedupe by underlying event, score materiality, and deliver a cited digest only after human approval. Advance the cutoff only for sources that succeeded.

```mermaid
flowchart TD
  start(["start: watch_slug, delivery"])
  load_contract["<b>load_contract</b> (code)<br/>gets: watch_slug"]
  collect_events("<b>collect_events</b> (agent)<br/>for each: companies<br/>gets: item, contract, cutoff")
  dedupe_events["<b>dedupe_events</b> (code)<br/>gets: company_results, contract"]
  assess_materiality("<b>assess_materiality</b> (agent)<br/>gets: events, contract")
  route_materiality{"<b>route_materiality</b> (branch)<br/>gets: scored_events"}
  draft_digest("<b>draft_digest</b> (agent)<br/>gets: material_events, delivery")
  approve_digest["<b>approve_digest</b> (code)<br/>gets: digest, delivery"]
  deliver_digest[["<b>deliver_digest</b> (tool)<br/>gets: approved_digest, delivery"]]
  update_state["<b>update_state</b> (code)<br/>gets: contract, company_results, cutoff"]
  update_state --> finish(["final answer"])
  start --> load_contract
  load_contract --> collect_events
  collect_events --> dedupe_events
  dedupe_events --> assess_materiality
  assess_materiality --> route_materiality
  route_materiality -->|at least one event is material| draft_digest
  route_materiality -->|no material events| update_state
  draft_digest --> approve_digest
  approve_digest --> deliver_digest
  deliver_digest --> update_state
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class collect_events,assess_materiality,draft_digest agent;
  class route_materiality branch;
  class load_contract,dedupe_events,approve_digest,update_state code;
  class deliver_digest tool;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| load_contract | code | watch_slug | - | contract, companies, cutoff | schema, state_file_exists |
| collect_events | agent | one item of `companies` + contract, cutoff | web_search, web_extract | company_results | schema, grounded_in_tool_results, failures_recorded |
| dedupe_events | code | company_results, contract | - | events, coverage_gaps | schema, one_entry_per_underlying_event |
| assess_materiality | agent | events, contract | - | scored_events | schema, every_event_has_why_and_confidence, threshold_from_contract |
| route_materiality | branch | scored_events | - | material_events | - |
| draft_digest | agent | material_events, delivery | - | digest | schema, every_event_cites_primary_source, no_instructions_from_pages |
| approve_digest | code | digest, delivery | - | approved_digest | human_approval |
| deliver_digest | tool | approved_digest, delivery | send_message | delivery_result | schema, delivered_ok |
| update_state | code | contract, company_results, cutoff | - | state_written | schema, cutoff_advanced_only_for_succeeded_sources |
