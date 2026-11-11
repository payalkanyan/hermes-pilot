# claude-code-delegation workflow (generated from the claude-code skill)

Delegate one coding task to the Claude Code CLI in a project directory, in print mode for one-shot work or interactive tmux mode for multi-turn work, gated by a command review and a login check, and report the result.

```mermaid
flowchart TD
  start(["start: task, project_dir, isolated_worktree"])
  plan_invocation("<b>plan_invocation</b> (agent)<br/>gets: task, project_dir, isolated_worktree")
  review_invocation("<b>review_invocation</b> (agent)<br/>gets: invocation")
  gate_review{"<b>gate_review</b> (branch)<br/>gets: review"}
  check_prereqs[["<b>check_prereqs</b> (tool)<br/>gets: invocation"]]
  gate_prereqs{"<b>gate_prereqs</b> (branch)<br/>gets: prereq_status"}
  gate_mode{"<b>gate_mode</b> (branch)<br/>gets: invocation"}
  run_print[["<b>run_print</b> (tool)<br/>gets: invocation, project_dir"]]
  run_interactive("<b>run_interactive</b> (agent)<br/>gets: invocation, project_dir")
  report["<b>report</b> (code)<br/>gets: invocation, run_result, review, prereq_status"]
  report --> finish(["final answer"])
  start --> plan_invocation
  plan_invocation --> review_invocation
  review_invocation --> gate_review
  gate_review -->|approved| check_prereqs
  gate_review -->|not approved| report
  check_prereqs --> gate_prereqs
  gate_prereqs -->|logged in| gate_mode
  gate_prereqs -->|not logged in| report
  gate_mode -->|mode is print| run_print
  gate_mode -->|mode is interactive| run_interactive
  run_print --> report
  run_interactive --> report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class check_prereqs,run_print tool;
  class plan_invocation,review_invocation,run_interactive agent;
  class report code;
  class gate_review,gate_prereqs,gate_mode branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| plan_invocation | agent | task, project_dir, isolated_worktree | read_file, search_files | invocation | schema, non_empty, no_bypass_flag, has_turn_limit, mode_justified |
| review_invocation | agent | invocation | read_file | review | schema, non_empty, review_covers_flags |
| gate_review | branch | review | - | gate_result | - |
| check_prereqs | tool | invocation | terminal | prereq_status | schema, non_empty, auth_logged_in |
| gate_prereqs | branch | prereq_status | - | prereq_gate | - |
| gate_mode | branch | invocation | - | mode_route | - |
| run_print | tool | invocation, project_dir | terminal | run_result | schema, non_empty, run_result_has_subtype |
| run_interactive | agent | invocation, project_dir | terminal | run_result | schema, non_empty, run_result_has_subtype, prompts_read_before_answer, no_blind_enter |
| report | code | invocation, run_result, review, prereq_status | - | final_answer | schema, reasons_are_bare_codes |
