# dogfood workflow (generated from the dogfood skill)

Run systematic exploratory QA of a web app in the browser, de-duplicate and rate the issues, and write a cited bug report to the output directory after the user approves the test plan.

```mermaid
flowchart TD
  start(["start: target_url, scope, output_dir"])
  plan_scope("<b>plan_scope</b> (agent)<br/>gets: target_url, scope")
  approve_plan("<b>approve_plan</b> (agent)<br/>gets: pages, scope")
  gate_approval{"<b>gate_approval</b> (branch)<br/>gets: approval"}
  create_output_dirs[["<b>create_output_dirs</b> (tool)<br/>gets: output_dir"]]
  explore_page("<b>explore_page</b> (agent)<br/>for each: pages<br/>gets: item, output_dir")
  categorize_issues("<b>categorize_issues</b> (agent)<br/>gets: page_results")
  assemble_report("<b>assemble_report</b> (agent)<br/>gets: issues, counts, page_results, pages, scope")
  write_report[["<b>write_report</b> (tool)<br/>gets: report_markdown, output_dir"]]
  write_report --> finish(["final answer"])
  start --> plan_scope
  plan_scope --> approve_plan
  approve_plan --> gate_approval
  gate_approval -->|approved| create_output_dirs
  gate_approval -->|not approved: report that no testing ran| assemble_report
  create_output_dirs --> explore_page
  explore_page --> categorize_issues
  categorize_issues --> assemble_report
  assemble_report --> write_report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class create_output_dirs,write_report tool;
  class plan_scope,approve_plan,explore_page,categorize_issues,assemble_report agent;
  class gate_approval branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| plan_scope | agent | target_url, scope | web_extract | pages | schema, non_empty, sitemap_from_fetched_page |
| approve_plan | agent | pages, scope | clarify | approval | schema, approval_recorded |
| gate_approval | branch | approval | - |  | - |
| create_output_dirs | tool | output_dir | terminal | output_dir_ready | screenshots_dir_exists |
| explore_page | agent | one item of `pages` + output_dir | browser_exec | page_results | schema, grounded_in_tool_results, console_hook_registered, interactions_exercised, evidence_saved |
| categorize_issues | agent | page_results | skill_view | issues, counts | schema, issues_deduplicated_sorted |
| assemble_report | agent | issues, counts, page_results, pages, scope | skill_view | report_markdown | schema, non_empty, report_complete |
| write_report | tool | report_markdown, output_dir | write_file | report_path | file_written |
