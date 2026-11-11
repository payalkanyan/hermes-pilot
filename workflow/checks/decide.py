"""Applies the six matching rules in code. Contract: reads {"inputs": {"facts": [...], "month": "2026-10"}} on stdin,
prints {"verdicts": [{"invoice_id", "verdict"}]}. It sees nothing but its declared inputs."""
import json, sys
def verdict(f, seen, month):
    if not f["date"].startswith(month): return "out_of_period"
    key = (f["supplier"], f["number"])
    if key in seen: return "duplicate"
    seen.add(key)
    sub = sum(l["qty"] * l["unit_price"] for l in f["inv_lines"])
    if abs(round(sub + f["tax"], 2) - f["total"]) > 0.005: return "arithmetic_error"
    if not f["po_found"]: return "missing_po"
    price = {l["sku"]: l["unit_price"] for l in f["po_lines"]}
    for l in f["inv_lines"]:
        if l["sku"] not in price or abs(l["unit_price"] - price[l["sku"]]) > 0.01 * price[l["sku"]] + 1e-9: return "price_mismatch"
    got = {}
    for d in f["delivered"]: got[d["sku"]] = got.get(d["sku"], 0) + d["qty"]
    for l in f["inv_lines"]:
        if l["qty"] > got.get(l["sku"], 0): return "quantity_exceeds_delivery"
    return "ok"
inp = json.load(sys.stdin)["inputs"]; seen = set()
print(json.dumps({"verdicts": [{"invoice_id": f["invoice_id"], "verdict": verdict(f, seen, inp["month"])} for f in inp["facts"]]}))
