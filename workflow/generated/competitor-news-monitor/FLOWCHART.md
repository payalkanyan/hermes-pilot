# competitor-news-monitor workflow (generated from the competitor-news-monitor skill)

Set up a competitor news watch once (watchlist, source coverage, state file, scheduled tick), then on each tick collect new evidence from the last cutoff, deduplicate by underlying event, score materiality, update the state file, and deliver a cited digest or stay silent.

```mermaid
flowchart TD
  start(["start: mode, watch_brief, state_path, deliver_to, all_clear"])
  mode_branch{"<b>mode_branch</b> (branch)<br/>gets: mode"}
  freeze_watchlist("<b>freeze_watchlist</b> (agent)<br/>gets: watch_brief")
  build_source_plan("<b>build_source_plan</b> (agent)<br/>gets: watch_contract")
  write_contract[["<b>write_contract</b> (tool)<br/>gets: watch_contract, source_plan, state_path"]]
  create_tick_job[["<b>create_tick_job</b> (tool)<br/>gets: state_path, state_file, deliver_to"]]
  load_contract("<b>load_contract</b> (agent)<br/>gets: state_path")
  collect_sources("<b>collect_sources</b> (agent)<br/>for each: source_list<br/>gets: item, cutoff")
  dedupe_and_assess("<b>dedupe_and_assess</b> (agent)<br/>gets: source_results, watch_contract")
  compute_run_state["<b>compute_run_state</b> (code)<br/>gets: source_results, scored_events, cutoff"]
  write_run_state[["<b>write_run_state</b> (tool)<br/>gets: run_state, state_path"]]
  deliver_digest("<b>deliver_digest</b> (agent)<br/>gets: scored_events, coverage_gaps, all_clear")
  finish["<b>finish</b> (code)<br/>gets: outcome"]
  finish --> finish(["final answer"])
  start --> mode_branch
  mode_branch -->|mode is setup| freeze_watchlist
  mode_branch -->|mode is tick| load_contract
  freeze_watchlist --> build_source_plan
  build_source_plan --> write_contract
  write_contract --> create_tick_job
  create_tick_job --> finish
  load_contract --> collect_sources
  collect_sources --> dedupe_and_assess
  dedupe_and_assess --> compute_run_state
  compute_run_state --> write_run_state
  write_run_state --> deliver_digest
  deliver_digest --> finish
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class write_contract,create_tick_job,write_run_state tool;
  class freeze_watchlist,build_source_plan,load_contract,collect_sources,dedupe_and_assess,deliver_digest agent;
  class compute_run_state,finish code;
  class mode_branch branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| mode_branch | branch | mode | - | mode | - |
| freeze_watchlist | agent | watch_brief | - | watch_contract | schema, non_empty, watchlist_complete |
| build_source_plan | agent | watch_contract | web_search, web_extract | source_plan | schema, non_empty, coverage_or_gap_per_category, job_postings_marked_weak |
| write_contract | tool | watch_contract, source_plan, state_path | write_file | state_file | schema, state_file_written |
| create_tick_job | tool | state_path, state_file, deliver_to | cronjob_manage | outcome | schema, job_created_with_contract_path |
| load_contract | agent | state_path | read_file | watch_contract, source_list, cutoff | schema, grounded_in_tool_results |
| collect_sources | agent | one item of `source_list` + cutoff | web_search, web_extract | source_results | schema, grounded_in_tool_results, failures_recorded_as_gaps, pagination_recorded, retrieved_content_is_data |
| dedupe_and_assess | agent | source_results, watch_contract | - | scored_events, coverage_gaps | schema, one_event_per_announcement, threshold_applied, facts_separated_from_interpretation, hiring_signals_not_confirmed |
| compute_run_state | code | source_results, scored_events, cutoff | - | run_state | schema, cutoff_advances_only_for_ok_sources |
| write_run_state | tool | run_state, state_path | write_file | run_state_file | schema, state_file_written |
| deliver_digest | agent | scored_events, coverage_gaps, all_clear | - | outcome | schema, non_empty, cites_primary_source_once, coverage_gaps_reported, silent_when_no_material_events |
| finish | code | outcome | - | final_answer | schema, non_empty |
