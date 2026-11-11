# test-driven-development workflow (generated from the test-driven-development skill)

Implement one feature or bug fix test-first, one behavior at a time (RED, GREEN, REFACTOR), and report verified results.

```mermaid
flowchart TD
  start(["start: feature_request, project_root, test_command, approval"])
  capture_behaviors("<b>capture_behaviors</b> (agent)<br/>gets: feature_request, project_root")
  route_approval{"<b>route_approval</b> (branch)<br/>gets: behaviors, approval"}
  red_test("<b>red_test</b> (agent)<br/>for each: approved_behaviors<br/>gets: item, project_root, test_command")
  verify_red["<b>verify_red</b> (code)<br/>gets: red_results"]
  green_impl("<b>green_impl</b> (agent)<br/>for each: red_verified<br/>gets: item, project_root, test_command")
  refactor("<b>refactor</b> (agent)<br/>gets: green_results, project_root, test_command")
  final_suite["<b>final_suite</b> (code)<br/>gets: refactor_results, test_command"]
  report["<b>report</b> (code)<br/>gets: red_verified, green_results, refactor_results, suite_result"]
  report --> finish(["final answer"])
  start --> capture_behaviors
  capture_behaviors --> route_approval
  route_approval -->|user approved| red_test
  route_approval -->|user did not approve| report
  red_test --> verify_red
  verify_red --> green_impl
  green_impl --> refactor
  refactor --> final_suite
  final_suite --> report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class route_approval branch;
  class capture_behaviors,red_test,green_impl,refactor agent;
  class verify_red,final_suite,report code;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| capture_behaviors | agent | feature_request, project_root | read_file, search_files | behaviors | schema, non_empty, no_files_written |
| route_approval | branch | behaviors, approval | - | approved_behaviors | human_approved |
| red_test | agent | one item of `approved_behaviors` + project_root, test_command | read_file, search_files, write_file, terminal | red_results | schema, test_failed_before_code, grounded_in_tool_results |
| verify_red | code | red_results | - | red_verified | schema, every_red_failed_for_missing_feature |
| green_impl | agent | one item of `red_verified` + project_root, test_command | read_file, search_files, patch, terminal | green_results | schema, target_test_passes, full_suite_no_regressions, grounded_in_tool_results |
| refactor | agent | green_results, project_root, test_command | read_file, search_files, patch, terminal | refactor_results | schema, suite_green_after_refactor |
| final_suite | code | refactor_results, test_command | - | suite_result | schema, exit_code_zero |
| report | code | red_verified, green_results, refactor_results, suite_result | - | final_answer | schema |
