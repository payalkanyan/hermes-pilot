# songwriting-and-ai-music workflow (generated from the songwriting-and-ai-music skill)

Turn a concept (original song or parody of a supplied song) into lyrics with structure tags and a Suno style prompt, get human approval, then save the package.

```mermaid
flowchart TD
  start(["start: concept, mode, mood, genre, source_lyrics"])
  check_mode{"<b>check_mode</b> (branch)<br/>gets: mode, source_lyrics"}
  map_skeleton("<b>map_skeleton</b> (agent)<br/>gets: source_lyrics")
  draft_lyrics("<b>draft_lyrics</b> (agent)<br/>gets: concept, mood, genre, skeleton, review_notes")
  build_suno_prompt("<b>build_suno_prompt</b> (agent)<br/>gets: title, lyrics, mood, genre")
  package_prompt["<b>package_prompt</b> (code)<br/>gets: title, lyrics_with_tags, style_field, exclude_field"]
  request_approval[["<b>request_approval</b> (tool)<br/>gets: review_package"]]
  route_approval{"<b>route_approval</b> (branch)<br/>gets: review_decision"}
  save_package["<b>save_package</b> (code)<br/>gets: review_package"]
  save_package --> finish(["final answer"])
  start --> check_mode
  check_mode -->|mode is parody| map_skeleton
  check_mode -->|mode is original| draft_lyrics
  map_skeleton --> draft_lyrics
  draft_lyrics --> build_suno_prompt
  build_suno_prompt --> package_prompt
  package_prompt --> request_approval
  request_approval --> route_approval
  route_approval -->|decision is approve| save_package
  route_approval -->|decision is redraft| draft_lyrics
  classDef agent fill:#fff3cd,stroke:#b58900;
  classDef code fill:#e7f1ff,stroke:#2b6cb0;
  classDef tool fill:#e6ffed,stroke:#2f855a;
  classDef branch fill:#fde8e8,stroke:#c53030;
  class map_skeleton,draft_lyrics,build_suno_prompt agent;
  class check_mode,route_approval branch;
  class package_prompt,save_package code;
  class request_approval tool;
```

## What each node receives

| Node | Type | Receives (only this) | Tools allowed | Produces | Checks |
|---|---|---|---|---|---|
| check_mode | branch | mode, source_lyrics | - | route_taken | schema, parody_has_source_lyrics |
| map_skeleton | agent | source_lyrics | - | skeleton | schema, line_count_matches_source |
| draft_lyrics | agent | concept, mood, genre, skeleton, review_notes | - | title, lyrics | schema, lyrics_under_3000_chars, metatags_in_allowed_list, no_artist_names |
| build_suno_prompt | agent | title, lyrics, mood, genre | - | style_field, exclude_field, lyrics_with_tags | schema, style_under_1000_chars, lyrics_under_3000_chars, no_artist_names |
| package_prompt | code | title, lyrics_with_tags, style_field, exclude_field | - | review_package | schema, all_fields_present |
| request_approval | tool | review_package | ask_user | review_decision, review_notes | schema, decision_is_approve_or_redraft_or_drop |
| route_approval | branch | review_decision | - | approval_route | schema |
| save_package | code | review_package | - | saved_path | schema, file_exists_after_write |
