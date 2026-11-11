# maps workflow (generated from the maps skill)

Answer one location question (geocode, reverse geocode, nearby places, distance, directions, timezone, area or bounding-box search) with scripts/maps_client.py using free OpenStreetMap data.

```mermaid
flowchart TD
  start(["start: request"])
  parse_request("<b>parse_request</b> (agent)<br/>gets: request")
  route_operation{"<b>route_operation</b> (branch)<br/>gets: parsed"}
  run_place_lookup["<b>run_place_lookup</b> (code)<br/>gets: parsed"]
  run_nearby["<b>run_nearby</b> (code)<br/>gets: parsed"]
  run_route["<b>run_route</b> (code)<br/>gets: parsed"]
  report_missing["<b>report_missing</b> (code)<br/>gets: parsed"]
  format_answer("<b>format_answer</b> (agent)<br/>gets: command_result")
  format_answer --> finish(["final answer"])
  start --> parse_request
  parse_request --> route_operation
  route_operation -->|operation is search| run_place_lookup
  route_operation -->|operation is nearby or bbox| run_nearby
  route_operation -->|operation is distance or directions| run_route
  route_operation -->|operation is needs_clarification| report_missing
  run_place_lookup --> format_answer
  run_nearby --> format_answer
  run_route --> format_answer
  report_missing --> format_answer
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class parse_request,format_answer agent;
  class route_operation branch;
  class run_place_lookup,run_nearby,run_route,report_missing code;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| parse_request | agent | request | - | parsed | schema, required_args_present |
| route_operation | branch | parsed | - | parsed | schema |
| run_place_lookup | code | parsed | - | command_result | schema, exit_code_zero, output_not_empty |
| run_nearby | code | parsed | - | command_result | schema, exit_code_zero, output_not_empty |
| run_route | code | parsed | - | command_result | schema, exit_code_zero, output_not_empty |
| report_missing | code | parsed | - | command_result | schema |
| format_answer | agent | command_result | - | final_answer | schema, grounded_in_command_output |
