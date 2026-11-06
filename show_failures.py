"""Prints WHY each failed run failed. Usage: python3 show_failures.py results/baseline.jsonl"""
import json, sys
for line in open(sys.argv[1]):
    g = json.loads(line)
    if g.get("infra_failed") or g["success"]:
        continue
    bad = [k for k, v in g["checks"].items() if not v]
    print(f"\n{g['task_id']} run {g['run']}: failed checks {bad}")
    d = g.get("detail")
    if not d:
        print("  (this run was saved before details were recorded; rerun it with --tag diag)"); continue
    for k, v in d.items():
        if v and k != "answer_len_chars":
            print(f"  {k}: {v}")
    print(f"  answer length: {d['answer_len_chars']} chars, tool calls: {g['tool_calls']}, api calls: {(g.get('usage') or {}).get('api_calls')}")