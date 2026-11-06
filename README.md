# Hermes pilot kit: invoice matching, baseline vs workflow

1. python3 gen_world.py                      # builds data/world.json + data/tasks.jsonl (8 tasks)
2. python3 run_suite.py --condition baseline --runs 3 --oracle   # self-test: must print 24/24
3. pip install "mcp<2"                        # for the fake tools server (mcp 2.x renamed FastMCP)
4. Register mock_server.py as an MCP server in Hermes (check Hermes docs for the exact config key), command:
   python /ABS/PATH/hermes-pilot/mock_server.py
5. Copy both skills into Hermes' skills folder (check Hermes docs/README for its location).
6. AGENT_CMD='<non-interactive hermes command with {prompt}>' python3 run_suite.py --condition baseline --runs 3
7. Same with --condition workflow.
Files: grade.py (deterministic grader), world_api.py (fake system), results/*.jsonl (raw answers per run).
