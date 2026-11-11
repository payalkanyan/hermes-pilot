# apple-notes workflow (generated from the apple-notes skill)

Run one Apple Notes operation through the memo CLI after the user approves the exact command, or report why it was not run.

```mermaid
flowchart TD
  start(["start: request, folder"])
  classify_request("<b>classify_request</b> (agent)<br/>gets: request, folder")
  route_scope{"<b>route_scope</b> (branch)<br/>gets: operation_plan"}
  compose_command("<b>compose_command</b> (agent)<br/>gets: operation_plan")
  approve_command[["<b>approve_command</b> (tool)<br/>gets: command_plan"]]
  route_approval{"<b>route_approval</b> (branch)<br/>gets: approval"}
  check_prereqs[["<b>check_prereqs</b> (tool)<br/>gets: -"]]
  route_prereq{"<b>route_prereq</b> (branch)<br/>gets: prereq_status"}
  run_memo[["<b>run_memo</b> (tool)<br/>gets: command_plan"]]
  report_result["<b>report_result</b> (code)<br/>gets: operation_plan, approval, prereq_status, memo_output"]
  report_result --> finish(["final answer"])
  start --> classify_request
  classify_request --> route_scope
  route_scope -->|applies to Apple Notes and operation is set| compose_command
  route_scope -->|out of scope or operation is none| report_result
  compose_command --> approve_command
  approve_command --> route_approval
  route_approval -->|approved| check_prereqs
  route_approval -->|declined| report_result
  check_prereqs --> route_prereq
  route_prereq -->|prerequisites pass| run_memo
  route_prereq -->|macOS or memo missing| report_result
  run_memo --> report_result
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class approve_command,check_prereqs,run_memo tool;
  class classify_request,compose_command agent;
  class report_result code;
  class route_scope,route_approval,route_prereq branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| classify_request | agent | request, folder | - | operation_plan | schema, non_empty |
| route_scope | branch | operation_plan | - | operation_plan | - |
| compose_command | agent | operation_plan | - | command_plan | schema, memo_command_is_documented, interactive_flag_matches |
| approve_command | tool | command_plan | clarify | approval | approval_recorded |
| route_approval | branch | approval | - | approval | - |
| check_prereqs | tool | - | terminal | prereq_status | prereq_macos_memo_present |
| route_prereq | branch | prereq_status | - | prereq_status | - |
| run_memo | tool | command_plan | terminal | memo_output | grounded_in_tool_results, exit_code_zero |
| report_result | code | operation_plan, approval, prereq_status, memo_output | - | final_answer | schema, non_empty |
