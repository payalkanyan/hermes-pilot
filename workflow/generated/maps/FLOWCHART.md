# maps workflow (generated from the maps skill)

Answer a location request (geocode, reverse geocode, nearby places, distance, directions, timezone, or bounding-box POI search) by running the maps_client.py script and presenting the results with map links.

```mermaid
flowchart TD
  start(["start: request"])
  parse_request("<b>parse_request</b> (agent)<br/>gets: request")
  gate_plan{"<b>gate_plan</b> (branch)<br/>gets: command_plan"}
  ask_user[["<b>ask_user</b> (tool)<br/>gets: command_plan"]]
  run_query[["<b>run_query</b> (tool)<br/>gets: approved_plan"]]
  check_open_now{"<b>check_open_now</b> (branch)<br/>gets: raw_result, approved_plan"}
  verify_hours("<b>verify_hours</b> (agent)<br/>gets: raw_result, approved_plan")
  present_results("<b>present_results</b> (agent)<br/>gets: raw_result, hours_check_needed, hours_note")
  present_results --> finish(["final answer"])
  start --> parse_request
  parse_request --> gate_plan
  gate_plan -->|plan is ready| run_query
  gate_plan -->|plan is not ready or ambiguous| ask_user
  ask_user -->|user answers| parse_request
  run_query --> check_open_now
  check_open_now -->|open-now question with missing or unclear hours| verify_hours
  check_open_now -->|otherwise| present_results
  verify_hours --> present_results
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class ask_user,run_query tool;
  class parse_request,verify_hours,present_results agent;
  class gate_plan,check_open_now branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| parse_request | agent | request | skill_view | command_plan | schema, non_empty, command_in_catalog, args_match_command |
| gate_plan | branch | command_plan | - | approved_plan | - |
| ask_user | tool | command_plan | clarify | clarification | non_empty |
| run_query | tool | approved_plan | terminal | raw_result | schema, exit_code_zero, json_output_parses, coordinates_in_range |
| check_open_now | branch | raw_result, approved_plan | - | hours_check_needed | - |
| verify_hours | agent | raw_result, approved_plan | web_search | hours_note | schema, non_empty, grounded_in_tool_results, hours_verified_or_marked_unknown |
| present_results | agent | raw_result, hours_check_needed, hours_note | - | final_answer | schema, non_empty, grounded_in_tool_results, numbered_list_with_maps_url |
