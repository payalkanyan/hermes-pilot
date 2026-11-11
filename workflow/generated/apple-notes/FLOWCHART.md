# apple-notes workflow (generated from the apple-notes skill)

Search, create, or export Apple Notes through the memo CLI on macOS, with human approval before any note is written or exported.

```mermaid
flowchart TD
  start(["start: action, query, folder, note_text, export_format"])
  preflight["<b>preflight</b> (code)<br/>gets: -"]
  route_action{"<b>route_action</b> (branch)<br/>gets: action"}
  search_notes["<b>search_notes</b> (code)<br/>gets: query, folder"]
  compose_note("<b>compose_note</b> (agent)<br/>gets: note_text, folder")
  approve_write["<b>approve_write</b> (code)<br/>gets: draft"]
  create_note["<b>create_note</b> (code)<br/>gets: approved_draft"]
  export_notes["<b>export_notes</b> (code)<br/>gets: folder, export_format"]
  approve_export["<b>approve_export</b> (code)<br/>gets: export_plan"]
  run_export["<b>run_export</b> (code)<br/>gets: approved_export"]
  report["<b>report</b> (code)<br/>gets: matches, created_note, export_path"]
  report --> finish(["final answer"])
  start --> preflight
  preflight --> route_action
  route_action -->|action is search| search_notes
  route_action -->|action is create| compose_note
  route_action -->|action is export| export_notes
  search_notes --> report
  compose_note --> approve_write
  approve_write --> create_note
  create_note --> report
  export_notes --> approve_export
  approve_export --> run_export
  run_export --> report
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class compose_note agent;
  class route_action branch;
  class preflight,search_notes,approve_write,create_note,export_notes,approve_export,run_export,report code;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| preflight | code | - | - | env_ok | schema, env_ok_is_true |
| route_action | branch | action | - | route | schema |
| search_notes | code | query, folder | - | matches | schema |
| compose_note | agent | note_text, folder | - | draft | schema, grounded_in_input |
| approve_write | code | draft | - | approved_draft | human_approved |
| create_note | code | approved_draft | - | created_note | schema, readback_matches_title |
| export_notes | code | folder, export_format | - | export_plan | schema, format_is_html_or_markdown |
| approve_export | code | export_plan | - | approved_export | human_approved |
| run_export | code | approved_export | - | export_path | schema, path_exists |
| report | code | matches, created_note, export_path | - | final_answer | schema |
