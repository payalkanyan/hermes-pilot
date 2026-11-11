# humanizer workflow (generated from the humanizer skill)

Rewrite a piece of text to remove AI writing patterns and add a natural voice, then return it inline or write it back to its file after approval.

```mermaid
flowchart TD
  start(["start: source, voice_sample"])
  resolve_source["<b>resolve_source</b> (code)<br/>gets: source"]
  calibrate_voice("<b>calibrate_voice</b> (agent)<br/>gets: voice_sample")
  rewrite_draft("<b>rewrite_draft</b> (agent)<br/>gets: draft_text, voice_profile")
  anti_ai_pass("<b>anti_ai_pass</b> (agent)<br/>gets: rewrite")
  route_output{"<b>route_output</b> (branch)<br/>gets: source_kind"}
  approve_write{"<b>approve_write</b> (branch)<br/>gets: final_text, source_path"}
  write_back[["<b>write_back</b> (tool)<br/>gets: source_path, final_text"]]
  final_report["<b>final_report</b> (code)<br/>gets: final_text, remaining_tells"]
  final_report --> finish(["final answer"])
  start --> resolve_source
  resolve_source --> calibrate_voice
  calibrate_voice --> rewrite_draft
  rewrite_draft --> anti_ai_pass
  anti_ai_pass --> route_output
  route_output -->|source_kind is file| approve_write
  route_output -->|source_kind is inline| final_report
  approve_write -->|user approves the write| write_back
  approve_write -->|user declines the write| final_report
  write_back --> final_report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class calibrate_voice,rewrite_draft,anti_ai_pass agent;
  class route_output,approve_write branch;
  class resolve_source,final_report code;
  class write_back tool;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| resolve_source | code | source | - | draft_text, source_kind, source_path | schema, non_empty |
| calibrate_voice | agent | voice_sample | read_file | voice_profile | schema, grounded_in_tool_results |
| rewrite_draft | agent | draft_text, voice_profile | - | rewrite, changes | schema, meaning_preserved |
| anti_ai_pass | agent | rewrite | - | final_text, remaining_tells | schema, no_new_facts |
| route_output | branch | source_kind | - | route | - |
| approve_write | branch | final_text, source_path | - | human_decision | human_approved_before_write |
| write_back | tool | source_path, final_text | write_file | write_result | schema, readback_matches |
| final_report | code | final_text, remaining_tells | - | final_answer | schema |
