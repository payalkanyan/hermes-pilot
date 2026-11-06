"""Applies the six matching rules in code. Usage: python decide.py facts.json --month 2026-10
facts.json is a JSON list of fact objects (schemas/fact.json) IN FOLDER LISTING ORDER. Prints a JSON list of verdicts."""
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
        if l["sku"] not in price or abs(l["unit_price"] - price[l["sku"]]) > 0.01 * price[l["sku"]] + 1e-9:
            return "price_mismatch"
    got = {}
    for d in f["delivered"]: got[d["sku"]] = got.get(d["sku"], 0) + d["qty"]
    for l in f["inv_lines"]:
        if l["qty"] > got.get(l["sku"], 0): return "quantity_exceeds_delivery"
    return "ok"
if __name__ == "__main__":
    facts = json.load(open(sys.argv[1])); month = sys.argv[sys.argv.index("--month") + 1]
    seen = set()
    print(json.dumps([{"invoice_id": f["invoice_id"], "verdict": verdict(f, seen, month)} for f in facts]))
