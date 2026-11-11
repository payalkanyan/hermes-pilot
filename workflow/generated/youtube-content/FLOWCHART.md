# youtube-content workflow (generated from the youtube-content skill)

Fetch a YouTube video's transcript with the youtube helper, turn it into the requested format (default summary), verify it, and return it. Stop with an explanation if any gate fails.

```mermaid
flowchart TD
  start(["start: video_url, output_format, language"])
  validate_url["<b>validate_url</b> (code)<br/>gets: video_url"]
  url_gate{"<b>url_gate</b> (branch)<br/>gets: url_valid"}
  ask_setup_approval[["<b>ask_setup_approval</b> (tool)<br/>gets: video_id"]]
  setup_gate{"<b>setup_gate</b> (branch)<br/>gets: approval_answer"}
  setup_and_fetch("<b>setup_and_fetch</b> (agent)<br/>gets: video_id, language")
  transcript_gate{"<b>transcript_gate</b> (branch)<br/>gets: transcript_status"}
  chunk_transcript["<b>chunk_transcript</b> (code)<br/>gets: transcript_text"]
  summarize_chunk("<b>summarize_chunk</b> (agent)<br/>for each: chunks<br/>gets: item")
  transform("<b>transform</b> (agent)<br/>gets: chunk_notes, output_format")
  verify_output("<b>verify_output</b> (agent)<br/>gets: formatted_output, chunk_notes")
  explain_failure("<b>explain_failure</b> (agent)<br/>gets: video_url, video_id, approval_answer, transcript_status")
  deliver["<b>deliver</b> (code)<br/>gets: final_output"]
  deliver --> finish(["final answer"])
  start --> validate_url
  validate_url --> url_gate
  url_gate -->|url is valid| ask_setup_approval
  url_gate -->|any other value| explain_failure
  ask_setup_approval --> setup_gate
  setup_gate -->|user explicitly approved| setup_and_fetch
  setup_gate -->|anything else| explain_failure
  setup_and_fetch --> transcript_gate
  transcript_gate -->|status is ok| chunk_transcript
  transcript_gate -->|any other status| explain_failure
  chunk_transcript --> summarize_chunk
  summarize_chunk --> transform
  transform --> verify_output
  verify_output --> deliver
  explain_failure --> deliver
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class ask_setup_approval tool;
  class setup_and_fetch,summarize_chunk,transform,verify_output,explain_failure agent;
  class validate_url,chunk_transcript,deliver code;
  class url_gate,setup_gate,transcript_gate branch;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| validate_url | code | video_url | - | video_id, url_valid | schema, url_is_youtube |
| url_gate | branch | url_valid | - |  | - |
| ask_setup_approval | tool | video_id | clarify | approval_answer | non_empty, user_approved |
| setup_gate | branch | approval_answer | - |  | - |
| setup_and_fetch | agent | video_id, language | terminal | transcript_text, transcript_language, transcript_status | schema, grounded_in_tool_results, import_check_passed, no_raw_pip |
| transcript_gate | branch | transcript_status | - |  | - |
| chunk_transcript | code | transcript_text | - | chunks | schema, non_empty |
| summarize_chunk | agent | one item of `chunks` | - | chunk_notes | schema, non_empty, timestamps_match_source |
| transform | agent | chunk_notes, output_format | - | formatted_output | schema, non_empty, format_matches_request, timestamps_match_source |
| verify_output | agent | formatted_output, chunk_notes | - | final_output | schema, non_empty, coherent_and_complete, timestamps_match_source |
| explain_failure | agent | video_url, video_id, approval_answer, transcript_status | - | final_output | schema, non_empty |
| deliver | code | final_output | - | answer | schema, non_empty |
