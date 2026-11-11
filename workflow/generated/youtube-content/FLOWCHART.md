# youtube-content workflow (generated from the youtube-content skill)

Turn one YouTube video's transcript into the requested format (summary by default), or report that no transcript is available.

```mermaid
flowchart TD
  start(["start: video_url, output_format, language"])
  fetch_transcript["<b>fetch_transcript</b> (code)<br/>gets: video_url, language"]
  check_transcript{"<b>check_transcript</b> (branch)<br/>gets: transcript"}
  fetch_any_language["<b>fetch_any_language</b> (code)<br/>gets: video_url"]
  check_fallback{"<b>check_fallback</b> (branch)<br/>gets: transcript"}
  report_unavailable["<b>report_unavailable</b> (code)<br/>gets: video_url"]
  chunk_transcript["<b>chunk_transcript</b> (code)<br/>gets: transcript"]
  summarize_chunk("<b>summarize_chunk</b> (agent)<br/>for each: chunks<br/>gets: item")
  transform_output("<b>transform_output</b> (agent)<br/>gets: chunk_notes, output_format, language_used")
  verify_output("<b>verify_output</b> (agent)<br/>gets: draft_output, chunk_notes")
  present_result["<b>present_result</b> (code)<br/>gets: result"]
  present_result --> finish(["final answer"])
  start --> fetch_transcript
  fetch_transcript --> check_transcript
  check_transcript -->|transcript is empty| fetch_any_language
  check_transcript -->|transcript is non-empty| chunk_transcript
  fetch_any_language --> check_fallback
  check_fallback -->|transcript still empty| report_unavailable
  check_fallback -->|transcript found| chunk_transcript
  report_unavailable --> present_result
  chunk_transcript --> summarize_chunk
  summarize_chunk --> transform_output
  transform_output --> verify_output
  verify_output --> present_result
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class summarize_chunk,transform_output,verify_output agent;
  class check_transcript,check_fallback branch;
  class fetch_transcript,fetch_any_language,report_unavailable,chunk_transcript,present_result code;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| fetch_transcript | code | video_url, language | - | transcript, language_used | schema |
| check_transcript | branch | transcript | - | transcript | schema |
| fetch_any_language | code | video_url | - | transcript, language_used | schema |
| check_fallback | branch | transcript | - | transcript, language_used | schema |
| report_unavailable | code | video_url | - | result | schema |
| chunk_transcript | code | transcript | - | chunks | schema, non_empty |
| summarize_chunk | agent | one item of `chunks` | - | chunk_notes | schema, grounded_in_source |
| transform_output | agent | chunk_notes, output_format, language_used | - | draft_output | schema, grounded_in_source, thread_posts_under_280_chars |
| verify_output | agent | draft_output, chunk_notes | - | result | schema, grounded_in_source |
| present_result | code | result | - | final_answer | schema |
