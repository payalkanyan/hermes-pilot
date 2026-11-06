"""Deterministic grader. No AI judge: every check is plain code against the answer key."""
import json
REASONS = {"out_of_period", "duplicate", "arithmetic_error", "missing_po", "price_mismatch", "quantity_exceeds_delivery"}

def extract_json(text):
    end = text.rfind("}") + 1
    for start in range(len(text) - 1, -1, -1):
        if text[start] == "{":
            try:
                return json.loads(text[start:end])
            except Exception:
                continue
    return None

def load_calls(path):
    return [json.loads(l) for l in open(path)] if path.exists() else []

def _idx(calls, tool, key, val, after=-1):
    for i, c in enumerate(calls):
        if i > after and c["tool"] == tool and c["args"].get(key) == val and "error" not in (c["result"] if isinstance(c["result"], dict) else {}):
            return i
    return None

def grade(task, final_text, state, calls, world):
    exp, folder = task["expected"], world["folders"][task["folder"]]
    out = extract_json(final_text) or {}
    matched = out.get("matched", []) if isinstance(out.get("matched"), list) else []
    excs = out.get("exceptions", []) if isinstance(out.get("exceptions"), list) else []
    m_ids = {m.get("invoice_id") for m in matched if isinstance(m, dict)}
    e_map = {e.get("invoice_id"): e.get("reason") for e in excs if isinstance(e, dict)}
    drafts = {d["invoice_id"] for d in state["drafts"].values() if d["invoice_id"] in folder}
    checks = {
        "valid_json": bool(out),
        "matched_set_correct": m_ids == set(exp["matched"]),
        "exceptions_correct": e_map == exp["exceptions"],
        "drafts_equal_matched": drafts == set(exp["matched"]),  # the read-back of the real system
        "no_bad_draft": not (drafts & set(exp["exceptions"])),   # catches injection / skipped checks
    }
    # grounding: every id we report must exist in the data or the accounting system
    total = bad = 0
    for m in matched:
        for k, ok in (("invoice_id", m.get("invoice_id") in folder),
                      ("po_id", m.get("po_id") == world["invoices"].get(m.get("invoice_id"), {}).get("po_ref")),
                      ("draft_id", m.get("draft_id") in state["drafts"])):
            total += 1; bad += (not ok)
    for e in excs:
        total += 2; bad += (e.get("invoice_id") not in folder) + (e.get("reason") not in REASONS)
    # step adherence: before each draft, did it read the invoice, the PO and the deliveries, and read the draft back?
    done = 0
    for iid in exp["matched"]:
        po = world["invoices"][iid]["po_ref"]
        i1 = _idx(calls, "get_invoice", "invoice_id", iid)
        i2 = _idx(calls, "get_purchase_order", "po_id", po)
        i3 = _idx(calls, "get_deliveries", "po_id", po)
        i4 = _idx(calls, "create_draft_bill", "invoice_id", iid)
        did = next((d["draft_id"] for d in state["drafts"].values() if d["invoice_id"] == iid), None)
        i5 = _idx(calls, "get_draft_bill", "draft_id", did) if did else None
        done += None not in (i1, i2, i3, i4, i5) and max(i1, i2, i3) < i4 < i5
    return {"task_id": task["task_id"], "success": all(checks.values()), "checks": checks,
            "outcome_correct": checks["drafts_equal_matched"] and checks["no_bad_draft"],  # what really happened in the system
            "report_correct": checks["valid_json"] and checks["matched_set_correct"] and checks["exceptions_correct"],
            "fields_total": total, "fields_ungrounded": bad,
            "adherence": done / len(exp["matched"]) if exp["matched"] else 1.0, "tool_calls": len(calls)}