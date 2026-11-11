# architecture-diagram workflow (generated from the architecture-diagram skill)

Turn a user's description of a software or cloud architecture into one self-contained dark-themed HTML file with inline SVG, saved to a user-chosen path after the user confirms the layout.

```mermaid
flowchart TD
  start(["start: system_description, output_path"])
  extract_model("<b>extract_model</b> (agent)<br/>gets: system_description")
  layout("<b>layout</b> (agent)<br/>gets: model")
  render_html("<b>render_html</b> (agent)<br/>gets: model, layout")
  confirm_write("<b>confirm_write</b> (agent)<br/>gets: output_path, model")
  route_approval{"<b>route_approval</b> (branch)<br/>gets: approval"}
  write_file[["<b>write_file</b> (tool)<br/>gets: output_path, html_text"]]
  verify_file["<b>verify_file</b> (code)<br/>gets: written_path"]
  stop_no_write["<b>stop_no_write</b> (code)<br/>gets: approval, final_report"]
  stop_no_write --> finish(["final answer"])
  start --> extract_model
  extract_model --> layout
  layout --> render_html
  render_html --> confirm_write
  confirm_write --> route_approval
  route_approval -->|user approved| write_file
  route_approval -->|user did not approve| stop_no_write
  write_file --> verify_file
  verify_file --> stop_no_write
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class extract_model,layout,render_html,confirm_write agent;
  class route_approval branch;
  class verify_file,stop_no_write code;
  class write_file tool;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| extract_model | agent | system_description | - | model | schema, ids_referenced_exist, no_unmentioned_components |
| layout | agent | model | - | layout | schema, no_overlapping_boxes, boundaries_contain_components, min_gap_40px |
| render_html | agent | model, layout | skill_view | html_text | schema, valid_html_document, no_script_tag, legend_below_boundaries |
| confirm_write | agent | output_path, model | - | approval | schema, explicit_user_approval |
| route_approval | branch | approval | - | approved_flag | - |
| write_file | tool | output_path, html_text | write_file | written_path | schema, file_exists_at_path |
| verify_file | code | written_path | - | final_report | schema, svg_present |
| stop_no_write | code | approval, final_report | - | summary | schema |
