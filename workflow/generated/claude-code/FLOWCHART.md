# claude-code-delegation workflow (generated from the claude-code skill)

Run one coding task through the Claude Code CLI in print mode inside a git repo, only after explicit approval, then verify the changes and report what happened.

```mermaid
flowchart TD
  start(["start: repo_path, task, user_decision"])
  preflight["<b>preflight</b> (code)<br/>gets: repo_path"]
  check_ready{"<b>check_ready</b> (branch)<br/>gets: preflight_report"}
  build_command["<b>build_command</b> (code)<br/>gets: task, repo_path"]
  approval_gate{"<b>approval_gate</b> (branch)<br/>gets: run_command, user_decision"}
  run_claude["<b>run_claude</b> (code)<br/>gets: run_command, repo_path"]
  verify_result["<b>verify_result</b> (code)<br/>gets: claude_result, repo_path"]
  review_diff("<b>review_diff</b> (agent)<br/>gets: task, repo_path, verification")
  report["<b>report</b> (code)<br/>gets: preflight_report, run_decision, claude_result, verification, review"]
  report --> finish(["final answer"])
  start --> preflight
  preflight --> check_ready
  check_ready -->|preflight passed| build_command
  check_ready -->|preflight failed| report
  build_command --> approval_gate
  approval_gate -->|user approved| run_claude
  approval_gate -->|user declined or unclear| report
  run_claude --> verify_result
  verify_result --> review_diff
  review_diff --> report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class review_diff agent;
  class check_ready,approval_gate branch;
  class preflight,build_command,run_claude,verify_result,report code;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| preflight | code | repo_path | - | preflight_report | schema, claude_version_present, auth_status_parsed, is_git_repo |
| check_ready | branch | preflight_report | - | preflight_report | - |
| build_command | code | task, repo_path | - | run_command | schema, print_mode_only, no_skip_permissions_flag, has_max_turns |
| approval_gate | branch | run_command, user_decision | - | run_decision | - |
| run_claude | code | run_command, repo_path | - | claude_result | schema, json_parsed, subtype_reported |
| verify_result | code | claude_result, repo_path | - | verification | schema, git_read_only |
| review_diff | agent | task, repo_path, verification | read_file, search_files | review | schema, grounded_in_tool_results |
| report | code | preflight_report, run_decision, claude_result, verification, review | - | final_answer | schema, absent_steps_marked_not_run, no_claims_beyond_tool_output |
