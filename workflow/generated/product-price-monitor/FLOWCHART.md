# product-price-monitor workflow (generated from the product-price-monitor skill)

Set up a price watch on one exact item with a verified baseline, then on each tick fetch the price, suppress duplicate alerts, and alert only when the all-in condition is met.

```mermaid
flowchart TD
  start(["start: item_url, variant, currency, max_all_in_price, cooldown_hours, destination, cadence"])
  build_contract["<b>build_contract</b> (code)<br/>gets: item_url, variant, currency, max_all_in_price, cooldown_hours, destination"]
  fetch_baseline("<b>fetch_baseline</b> (agent)<br/>gets: contract")
  approve_baseline{"<b>approve_baseline</b> (branch)<br/>gets: contract, baseline"}
  write_state[["<b>write_state</b> (tool)<br/>gets: contract, baseline"]]
  create_schedule[["<b>create_schedule</b> (tool)<br/>gets: state_path, cadence, destination"]]
  fetch_current("<b>fetch_current</b> (agent)<br/>gets: contract, state_path")
  compare_observation["<b>compare_observation</b> (code)<br/>gets: observation, contract, state_path"]
  route_alert{"<b>route_alert</b> (branch)<br/>gets: decision"}
  deliver_alert[["<b>deliver_alert</b> (tool)<br/>gets: alert_payload, destination"]]
  save_state[["<b>save_state</b> (tool)<br/>gets: updated_state, state_path"]]
  report_outcome["<b>report_outcome</b> (code)<br/>gets: approval"]
  report_outcome --> finish(["final answer"])
  start --> build_contract
  build_contract --> fetch_baseline
  fetch_baseline --> approve_baseline
  approve_baseline -->|user approves and baseline.failed is false| write_state
  approve_baseline -->|user declines or baseline failed| report_outcome
  write_state --> create_schedule
  create_schedule --> fetch_current
  fetch_current --> compare_observation
  compare_observation --> route_alert
  route_alert -->|decision is alert| deliver_alert
  route_alert -->|decision is silent or failed| save_state
  deliver_alert --> save_state
  save_state --> report_outcome
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class fetch_baseline,fetch_current agent;
  class approve_baseline,route_alert branch;
  class build_contract,compare_observation,report_outcome code;
  class write_state,create_schedule,deliver_alert,save_state tool;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| build_contract | code | item_url, variant, currency, max_all_in_price, cooldown_hours, destination | - | contract | schema, variant_nonempty, currency_is_iso_code, threshold_positive |
| fetch_baseline | agent | contract | web_extract | baseline | schema, grounded_in_tool_results, variant_matches_contract |
| approve_baseline | branch | contract, baseline | - | approval | - |
| write_state | tool | contract, baseline | write_file | state_path | schema, file_parses_as_json, contract_matches_state |
| create_schedule | tool | state_path, cadence, destination | cronjob_manage | job_id | schema, job_listed_with_cadence |
| fetch_current | agent | contract, state_path | web_extract | observation | schema, grounded_in_tool_results, variant_matches_contract |
| compare_observation | code | observation, contract, state_path | - | decision, alert_payload, updated_state | schema, deterministic_replay, no_overwrite_on_failed_fetch, same_offer_not_realerted_within_cooldown, currency_matches_contract |
| route_alert | branch | decision | - | route_result | - |
| deliver_alert | tool | alert_payload, destination | send_message | delivery | schema, destination_matches_contract, payload_has_all_in_price_currency_timestamp_link, never_claims_reserved_inventory |
| save_state | tool | updated_state, state_path | write_file | saved_state | schema, last_good_not_overwritten_by_error, file_parses_as_json |
| report_outcome | code | approval | - | result | schema |
