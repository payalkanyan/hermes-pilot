"""Watches the Hermes session store and turns each newly finished task into a workflow
automatically — the way Hermes saves a skill after a task, but as a SIDE-CAR with zero
changes to Hermes core (the brief's ground rule: prefer wrappers over editing Hermes).

A session counts as a finished task when ALL of these hold:
  - it has ended (ended_at is set in ~/.hermes/state.db, which is only ever read, read-only)
  - it is not a delegation helper (no parent_session_id)
  - it made at least --min-tool-calls tool calls (default 3; the generator's own model
    calls and plain chats make 0, so they can never trigger a loop)
  - its title does not match --ignore-title (default: the trace-converter's own sessions)
  - its exported trace ends with a final assistant answer (checked with the M1 parser)

For each one, the watcher runs `hermes sessions export --format md` and feeds the file to
generate_from_session.generate(), so the workflow spec + FLOWCHART.md appear on their own
under workflow/generated_from_sessions/.

  AGENT_CMD='hermes -z {prompt} --usage-file {usage} --provider openrouter -m anthropic/claude-haiku-5.5 --reasoning medium --ignore-rules' \\
  python3 watch_sessions.py --once              one pass, then exit (good for cron or testing)
  python3 watch_sessions.py --interval 20       poll forever, every 20 seconds
  python3 watch_sessions.py --once --dry-run    export and check candidates, call no model

On the first run nothing old is converted: the watcher starts from "now" (use --since all
to process history). State lives in workflow/generated_from_sessions/.watcher_state.json.
Needs: pip install pyyaml"""
import argparse, json, pathlib, re, sqlite3, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from generate_from_session import parse_session, generate

OUT = HERE / "generated_from_sessions"
STATE = OUT / ".watcher_state.json"
EXPORTS = OUT / "exports"

def load_state():
    try: return json.loads(STATE.read_text())
    except Exception: return {"last_ended": None, "done": {}}

def save_state(st):
    OUT.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(st, indent=1))

def finished_sessions(db_path, after):
    db = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = db.execute(
            "select id, title, cwd, ended_at, tool_call_count from sessions "
            "where ended_at is not null and ended_at > ? and parent_session_id is null "
            "and hidden = 0 order by ended_at", (after,)).fetchall()
    finally:
        db.close()
    return [dict(zip(("id", "title", "cwd", "ended_at", "tool_calls"), r)) for r in rows]

def export_session(sid):
    """Exports one session as markdown into EXPORTS and returns the file path, or None."""
    EXPORTS.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(["hermes", "sessions", "export", "--format", "md",
                        "--session-id", sid, "--yes", str(EXPORTS)],
                       capture_output=True, text=True, timeout=120)
    files = sorted(EXPORTS.glob(f"*{sid}*.md"), key=lambda p: p.stat().st_mtime)
    if not files:
        print(f"  export failed for {sid[:20]}…: {(r.stderr or r.stdout).strip()[:200]}")
        return None
    return files[-1]

def has_final_answer(path):
    """True when the exported trace ends with a non-empty assistant message."""
    try:
        _, evs = parse_session(path.read_text(encoding="utf-8"))
    except Exception as ex:
        print(f"  could not parse export: {ex}"); return False
    finals = [e for e in evs if e[0] == "assistant"]
    return bool(finals and finals[-1][1].strip())

def run_once(a, st):
    after = st["last_ended"] if st["last_ended"] is not None else (0.0 if a.since == "all" else time.time())
    if st["last_ended"] is None:
        st["last_ended"] = after
        save_state(st)
        if a.since != "all":
            print(f"first run: watching for sessions that finish from now on (use --since all for history)")
    converted = 0
    for s in finished_sessions(a.db, after):
        st["last_ended"] = max(st["last_ended"], s["ended_at"])
        sid, title = s["id"], s["title"] or ""
        if sid in st["done"]: continue
        why = None
        if s["tool_calls"] < a.min_tool_calls: why = f"only {s['tool_calls']} tool calls"
        elif re.search(a.ignore_title, title): why = "title matches --ignore-title"
        elif a.cwd_filter and a.cwd_filter not in (s["cwd"] or ""): why = "outside --cwd-filter"
        if why:
            st["done"][sid] = {"skipped": why}; save_state(st)
            if a.verbose: print(f"skip  {title[:50]!r}: {why}")
            continue
        print(f"task finished: {title[:60]!r} ({s['tool_calls']} tool calls) -> exporting")
        path = export_session(sid)
        if path is None or not has_final_answer(path):
            st["done"][sid] = {"skipped": "no export or no final answer"}; save_state(st)
            print("  skipped: no export or no final assistant answer (not a completed task)")
            continue
        if a.dry_run:
            st["done"][sid] = {"dry_run": str(path)}; save_state(st)
            print(f"  dry run: would generate a workflow from {path.name}")
            continue
        row = generate(path)
        st["done"][sid] = row; save_state(st)
        converted += 1
        print(f"  {'VALID' if row['valid'] else 'INVALID'} workflow '{row['slug']}' "
              f"nodes={row['nodes']} attempts={row['attempts']} cost=${row['cost_usd']}"
              + (f" | {'; '.join(row['errors'][:2])}" if row["errors"] else ""))
    save_state(st)
    return converted

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", default=str(pathlib.Path.home() / ".hermes" / "state.db"))
    p.add_argument("--interval", type=float, default=15, help="seconds between polls")
    p.add_argument("--once", action="store_true", help="one pass, then exit")
    p.add_argument("--dry-run", action="store_true", help="export and check, but call no model")
    p.add_argument("--since", choices=["now", "all"], default="now", help="first-run baseline")
    p.add_argument("--min-tool-calls", type=int, default=3)
    p.add_argument("--ignore-title", default=r"^Convert agent trace", help="regex of session titles to skip")
    p.add_argument("--cwd-filter", default="", help="only sessions whose working directory contains this")
    p.add_argument("--verbose", action="store_true", help="log skipped sessions too")
    a = p.parse_args()
    st = load_state()
    print(f"watching {a.db} (poll every {a.interval:g}s)" if not a.once else f"single pass over {a.db}")
    while True:
        try:
            run_once(a, st)
        except KeyboardInterrupt:
            raise
        except Exception as ex:
            print(f"watcher error (will keep running): {type(ex).__name__}: {ex}")
        if a.once: break
        time.sleep(a.interval)

if __name__ == "__main__":
    main()
