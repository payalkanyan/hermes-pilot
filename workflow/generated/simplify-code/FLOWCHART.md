# simplify-code workflow (generated from the simplify-code skill)

Review the user's recent code changes with four parallel narrow reviewers (reuse, quality, efficiency, altitude), resolve their findings into SAFE, CAREFUL and RISKY tiers, apply only the user-approved SAFE and CAREFUL fixes with test verification, and report the rest.

```mermaid
flowchart TD
  start(["start: repo_path, scope, focus, dry_run"])
  capture_diff["<b>capture_diff</b> (code)<br/>gets: repo_path, scope"]
  size_gate{"<b>size_gate</b> (branch)<br/>gets: diff_stats"}
  await_scope_approval["<b>await_scope_approval</b> (code)<br/>gets: diff_stats, scope"]
  define_reviewers["<b>define_reviewers</b> (code)<br/>gets: focus"]
  review("<b>review</b> (agent)<br/>for each: reviewer_angles<br/>gets: item, diff_text, repo_path")
  merge_findings["<b>merge_findings</b> (code)<br/>gets: reviewer_findings"]
  resolve_plan("<b>resolve_plan</b> (agent)<br/>gets: merged_findings, focus")
  approve_plan["<b>approve_plan</b> (code)<br/>gets: plan"]
  route_after_approval{"<b>route_after_approval</b> (branch)<br/>gets: approved_plan, dry_run"}
  apply_fixes("<b>apply_fixes</b> (agent)<br/>gets: approved_plan, repo_path")
  run_checks["<b>run_checks</b> (code)<br/>gets: repo_path, apply_log"]
  report["<b>report</b> (code)<br/>gets: approved_plan, apply_log, test_result"]
  report --> finish(["final answer"])
  start --> capture_diff
  capture_diff --> size_gate
  size_gate -->|more than 2000 changed lines| await_scope_approval
  size_gate -->|2000 or fewer changed lines| define_reviewers
  await_scope_approval --> define_reviewers
  define_reviewers --> review
  review --> merge_findings
  merge_findings --> resolve_plan
  resolve_plan --> approve_plan
  approve_plan --> route_after_approval
  route_after_approval -->|not a dry run and at least one SAFE or CAREFUL item approved| apply_fixes
  route_after_approval -->|dry run, or nothing approved| report
  apply_fixes --> run_checks
  run_checks --> report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class size_gate,route_after_approval branch;
  class review,resolve_plan,apply_fixes agent;
  class capture_diff,await_scope_approval,define_reviewers,merge_findings,approve_plan,run_checks,report code;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| capture_diff | code | repo_path, scope | - | diff_text, diff_stats | schema, non_empty_diff |
| size_gate | branch | diff_stats | - | diff_stats | - |
| await_scope_approval | code | diff_stats, scope | - | scope_approved | human_approved |
| define_reviewers | code | focus | - | reviewer_angles | schema, at_most_four_angles |
| review | agent | one item of `reviewer_angles` + diff_text, repo_path | read_file, search_files, terminal | reviewer_findings | schema, evidence_has_file_and_line, findings_grounded_in_search |
| merge_findings | code | reviewer_findings | - | merged_findings | schema, no_duplicate_locations |
| resolve_plan | agent | merged_findings, focus | read_file, search_files, terminal | plan | schema, every_item_has_file_and_line, tier_matches_risk_rule |
| approve_plan | code | plan | - | approved_plan | human_approved, no_risky_item_auto_approved |
| route_after_approval | branch | approved_plan, dry_run | - | approved_plan | - |
| apply_fixes | agent | approved_plan, repo_path | read_file, patch, terminal | apply_log | schema, only_approved_items_touched, no_risky_item_applied |
| run_checks | code | repo_path, apply_log | - | test_result | schema, exit_codes_recorded |
| report | code | approved_plan, apply_log, test_result | - | final_report | schema, every_skipped_item_has_reason |
