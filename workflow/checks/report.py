"""Contract: {"inputs": {"confirmed_drafts": [...], "exceptions": [...]}} -> {"final_answer": {"matched": [...], "exceptions": [...]}}."""
import json, sys
inp = json.load(sys.stdin)["inputs"]
print(json.dumps({"final_answer": {"matched": [{"invoice_id": d["invoice_id"], "po_id": d["po_id"], "draft_id": d["draft_id"]} for d in inp["confirmed_drafts"]],
                                   "exceptions": inp["exceptions"]}}))
