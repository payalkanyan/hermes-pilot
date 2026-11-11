# architecture-diagram workflow (generated from the architecture-diagram skill)

Generate a dark-themed, self-contained HTML file with inline SVG that renders a technical architecture diagram from the user's description of components and connections, then tell the user where it is saved.

```mermaid
flowchart TD
  start(["start: architecture_description, output_path"])
  scope_check("<b>scope_check</b> (agent)<br/>gets: architecture_description")
  scope_branch{"<b>scope_branch</b> (branch)<br/>gets: diagram_spec"}
  plan_layout("<b>plan_layout</b> (agent)<br/>gets: in_scope_spec")
  build_html("<b>build_html</b> (agent)<br/>gets: layout, in_scope_spec")
  resolve_path["<b>resolve_path</b> (code)<br/>gets: output_path, in_scope_spec"]
  confirm_write{"<b>confirm_write</b> (branch)<br/>gets: file_path, html_text"}
  write_diagram[["<b>write_diagram</b> (tool)<br/>gets: file_path, html_text"]]
  report_saved["<b>report_saved</b> (code)<br/>gets: saved_path"]
  report_out_of_scope["<b>report_out_of_scope</b> (code)<br/>gets: in_scope_spec"]
  report_out_of_scope --> finish(["final answer"])
  start --> scope_check
  scope_check --> scope_branch
  scope_branch -->|in_scope is true| plan_layout
  scope_branch -->|any other value| report_out_of_scope
  plan_layout --> build_html
  build_html --> resolve_path
  resolve_path --> confirm_write
  confirm_write -->|user approves the path| write_diagram
  confirm_write -->|user declines| report_out_of_scope
  write_diagram --> report_saved
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class write_diagram tool;
  class scope_check,plan_layout,build_html agent;
  class resolve_path,report_saved,report_out_of_scope code;
  class scope_branch,confirm_write branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| scope_check | agent | architecture_description | - | diagram_spec | schema, non_empty, scope_is_in_scope |
| scope_branch | branch | diagram_spec | - | in_scope_spec | - |
| plan_layout | agent | in_scope_spec | - | layout | schema, non_empty, no_overlapping_components, legend_below_boundaries, bus_in_gap_between_services |
| build_html | agent | layout, in_scope_spec | skill_view | html_text | schema, non_empty, no_javascript, no_external_resources_except_google_fonts, uses_semantic_colors, legend_outside_boundaries |
| resolve_path | code | output_path, in_scope_spec | - | file_path | schema, non_empty |
| confirm_write | branch | file_path, html_text | - | write_approved | non_empty |
| write_diagram | tool | file_path, html_text | write_file | saved_path | schema, grounded_in_tool_results |
| report_saved | code | saved_path | - | final_answer | schema, non_empty |
| report_out_of_scope | code | in_scope_spec | - | final_answer | schema, non_empty |
