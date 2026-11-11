# systematic-debugging workflow (generated from the systematic-debugging skill)

Find the root cause of one bug through a tight red/green feedback loop, confirm it with a minimal test, get user approval, then apply and verify one fix.

```mermaid
flowchart TD
  start(["start: symptom, repo_path"])
  build_loop("<b>build_loop</b> (agent)<br/>gets: symptom, repo_path")
  minimize_repro("<b>minimize_repro</b> (agent)<br/>gets: loop, symptom, repo_path")
  gather_evidence("<b>gather_evidence</b> (agent)<br/>gets: minimal_repro, repo_path")
  form_hypotheses("<b>form_hypotheses</b> (agent)<br/>gets: evidence, minimal_repro")
  test_hypotheses("<b>test_hypotheses</b> (agent)<br/>gets: hypotheses, loop, repo_path")
  route_hypothesis{"<b>route_hypothesis</b> (branch)<br/>gets: hypothesis_result"}
  request_approval{"<b>request_approval</b> (branch)<br/>gets: confirmed_cause"}
  write_regression_test("<b>write_regression_test</b> (agent)<br/>gets: approved_fix, minimal_repro, repo_path")
  apply_fix("<b>apply_fix</b> (agent)<br/>gets: approved_fix, regression_test, repo_path")
  verify_fix("<b>verify_fix</b> (agent)<br/>gets: loop, regression_test, fix_summary, repo_path")
  report["<b>report</b> (code)<br/>gets: final_status"]
  report --> finish(["final answer"])
  start --> build_loop
  build_loop --> minimize_repro
  minimize_repro --> gather_evidence
  gather_evidence --> form_hypotheses
  form_hypotheses --> test_hypotheses
  test_hypotheses --> route_hypothesis
  route_hypothesis -->|outcome is confirmed| request_approval
  route_hypothesis -->|outcome is falsified or inconclusive| report
  request_approval -->|user approves| write_regression_test
  request_approval -->|user declines| report
  write_regression_test --> apply_fix
  apply_fix --> verify_fix
  verify_fix --> report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class route_hypothesis,request_approval branch;
  class build_loop,minimize_repro,gather_evidence,form_hypotheses,test_hypotheses,write_regression_test,apply_fix,verify_fix agent;
  class report code;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| build_loop | agent | symptom, repo_path | terminal, read_file, search_files | loop | schema, loop_is_red |
| minimize_repro | agent | loop, symptom, repo_path | terminal, read_file | minimal_repro | schema, still_red |
| gather_evidence | agent | minimal_repro, repo_path | terminal, read_file, search_files | evidence | schema, grounded_in_tool_results |
| form_hypotheses | agent | evidence, minimal_repro | read_file, search_files | hypotheses | schema, each_has_prediction |
| test_hypotheses | agent | hypotheses, loop, repo_path | terminal, read_file | hypothesis_result | schema, probes_reverted, at_most_3_probes |
| route_hypothesis | branch | hypothesis_result | - | confirmed_cause, final_status | - |
| request_approval | branch | confirmed_cause | - | approved_fix, final_status | - |
| write_regression_test | agent | approved_fix, minimal_repro, repo_path | read_file, write_file, terminal | regression_test | schema, fails_before_fix |
| apply_fix | agent | approved_fix, regression_test, repo_path | read_file, patch, terminal | fix_summary | schema, single_root_cause_change |
| verify_fix | agent | loop, regression_test, fix_summary, repo_path | terminal | final_status | schema, loop_green, full_suite_green |
| report | code | final_status | - | final_answer | schema |
