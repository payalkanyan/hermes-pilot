"""Contract: {"inputs": {"exception_items": [{"invoice_id", "verdict"}]}} -> {"exceptions": [{"invoice_id", "reason"}]}."""
import json, sys
inp = json.load(sys.stdin)["inputs"]
print(json.dumps({"exceptions": [{"invoice_id": e["invoice_id"], "reason": e["verdict"]} for e in inp["exception_items"]]}))
