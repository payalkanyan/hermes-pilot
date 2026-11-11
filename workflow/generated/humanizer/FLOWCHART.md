# humanizer workflow (generated from the humanizer skill)

Rewrite user-supplied text to remove AI writing patterns and add a real voice, preserve its meaning, show the rewrite, and apply it to a file only after the user approves.

```mermaid
flowchart TD
  start(["start: source_text, source_file, voice_sample"])
  collect_source("<b>collect_source</b> (agent)<br/>gets: source_text, source_file, voice_sample")
  voice_branch{"<b>voice_branch</b> (branch)<br/>gets: voice_sample_text"}
  analyze_voice("<b>analyze_voice</b> (agent)<br/>gets: voice_sample_text")
  scan_patterns("<b>scan_patterns</b> (agent)<br/>gets: draft_text")
  rewrite("<b>rewrite</b> (agent)<br/>gets: draft_text, pattern_hits, voice_profile")
  anti_ai_pass("<b>anti_ai_pass</b> (agent)<br/>gets: revised_text")
  present_changes("<b>present_changes</b> (agent)<br/>gets: draft_text, final_text, source_file")
  confirm_edit("<b>confirm_edit</b> (agent)<br/>gets: change_summary, source_file")
  route_decision{"<b>route_decision</b> (branch)<br/>gets: decision"}
  apply_file("<b>apply_file</b> (agent)<br/>gets: source_file, draft_text, final_text")
  report["<b>report</b> (code)<br/>gets: final_text, remaining_tells, change_summary, applied_path"]
  report --> finish(["final answer"])
  start --> collect_source
  collect_source --> voice_branch
  voice_branch -->|voice sample provided| analyze_voice
  voice_branch -->|no voice sample| scan_patterns
  analyze_voice --> scan_patterns
  scan_patterns --> rewrite
  rewrite --> anti_ai_pass
  anti_ai_pass --> present_changes
  present_changes --> confirm_edit
  confirm_edit --> route_decision
  route_decision -->|decision is apply_to_file| apply_file
  route_decision -->|decision is inline_only| report
  apply_file --> report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class collect_source,analyze_voice,scan_patterns,rewrite,anti_ai_pass,present_changes,confirm_edit,apply_file agent;
  class report code;
  class voice_branch,route_decision branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| collect_source | agent | source_text, source_file, voice_sample | read_file | draft_text, voice_sample_text | schema, non_empty, grounded_in_tool_results |
| voice_branch | branch | voice_sample_text | - | voice_sample_text | - |
| analyze_voice | agent | voice_sample_text | - | voice_profile | schema, non_empty |
| scan_patterns | agent | draft_text | skill_view | pattern_hits | schema, all_patterns_reported, grounded_in_tool_results |
| rewrite | agent | draft_text, pattern_hits, voice_profile | - | revised_text | schema, non_empty, meaning_preserved, voice_matches_profile, has_personality |
| anti_ai_pass | agent | revised_text | - | final_text, remaining_tells | schema, non_empty, tells_addressed, meaning_preserved |
| present_changes | agent | draft_text, final_text, source_file | - | change_summary | schema, non_empty |
| confirm_edit | agent | change_summary, source_file | clarify | decision | schema |
| route_decision | branch | decision | - | decision | - |
| apply_file | agent | source_file, draft_text, final_text | patch | applied_path | schema, grounded_in_tool_results, diff_matches_final_text |
| report | code | final_text, remaining_tells, change_summary, applied_path | - | final_answer | schema, shows_rewrite |
