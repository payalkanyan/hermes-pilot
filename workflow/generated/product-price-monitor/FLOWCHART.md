# product-price-monitor workflow (generated from the product-price-monitor skill)

Set up a price watch on one concrete item (baseline fetch, contract file, recurring cron job), and on each scheduled tick re-fetch the item, compare the all-in price and availability with stored state, alert only on a new qualifying condition, and never overwrite the last good observation with an error.

```mermaid
flowchart TD
  start(["start: mode, item_description, alert_condition, watch_slug, deliver"])
  route_mode{"<b>route_mode</b> (branch)<br/>gets: mode"}
  define_item("<b>define_item</b> (agent)<br/>gets: item_description")
  define_condition("<b>define_condition</b> (agent)<br/>gets: alert_condition, item_contract")
  baseline_fetch("<b>baseline_fetch</b> (agent)<br/>gets: item_contract, alert_rule")
  write_contract[["<b>write_contract</b> (tool)<br/>gets: watch_contract, watch_slug"]]
  create_job[["<b>create_job</b> (tool)<br/>gets: contract_path, watch_slug, deliver"]]
  tick_fetch("<b>tick_fetch</b> (agent)<br/>gets: watch_slug")
  compare_and_decide["<b>compare_and_decide</b> (code)<br/>gets: tick_observation, watch_slug"]
  gate_alert{"<b>gate_alert</b> (branch)<br/>gets: alert_decision"}
  deliver_alert("<b>deliver_alert</b> (agent)<br/>gets: alert_decision, tick_observation")
  record_state[["<b>record_state</b> (tool)<br/>gets: state_update, watch_slug"]]
  report["<b>report</b> (code)<br/>gets: job_id, alert_message, state_written"]
  report --> finish(["final answer"])
  start --> route_mode
  route_mode -->|mode is setup| define_item
  route_mode -->|mode is tick| tick_fetch
  define_item --> define_condition
  define_condition --> baseline_fetch
  baseline_fetch --> write_contract
  write_contract --> create_job
  create_job --> report
  tick_fetch --> compare_and_decide
  compare_and_decide --> gate_alert
  gate_alert -->|alert condition met| deliver_alert
  gate_alert -->|any other decision| record_state
  deliver_alert --> record_state
  record_state --> report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class write_contract,create_job,record_state tool;
  class define_item,define_condition,baseline_fetch,tick_fetch,deliver_alert agent;
  class compare_and_decide,report code;
  class route_mode,gate_alert branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| route_mode | branch | mode | - | route | mode_is_setup_or_tick |
| define_item | agent | item_description | - | item_contract | schema, non_empty, item_pins_variant |
| define_condition | agent | alert_condition, item_contract | - | alert_rule | schema, non_empty, condition_decides_synthetic_examples |
| baseline_fetch | agent | item_contract, alert_rule | web_extract, browser_exec | watch_contract | schema, non_empty, baseline_fetch_succeeded, baseline_matches_contract |
| write_contract | tool | watch_contract, watch_slug | write_file | contract_path | schema |
| create_job | tool | contract_path, watch_slug, deliver | cronjob_manage | job_id | schema, cadence_respects_site_limits |
| tick_fetch | agent | watch_slug | read_file, web_extract, browser_exec | tick_observation | schema, grounded_in_tool_results |
| compare_and_decide | code | tick_observation, watch_slug | - | alert_decision, state_update | schema, compare_is_deterministic, state_file_preserves_last_good |
| gate_alert | branch | alert_decision | - | route | schema |
| deliver_alert | agent | alert_decision, tick_observation | - | alert_message | schema, non_empty, alert_has_required_fields |
| record_state | tool | state_update, watch_slug | write_file | state_written | schema |
| report | code | job_id, alert_message, state_written | - | final_answer | schema, non_empty |
