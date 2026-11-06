"""The fake invoice system. Plain Python so it can be tested without MCP.
mock_server.py exposes these same functions to Hermes as MCP tools."""
import json, os, pathlib
ROOT = pathlib.Path(__file__).parent
WORLD = json.loads((ROOT / "data" / "world.json").read_text())
STATE = pathlib.Path(os.environ.get("MOCK_STATE", ROOT / "state" / "state.json"))
LOG = pathlib.Path(os.environ.get("MOCK_LOG", ROOT / "state" / "calls.jsonl"))

def _state():
    return json.loads(STATE.read_text()) if STATE.exists() else {"drafts": {}}

def _log(tool, args, result):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps({"tool": tool, "args": args, "result": result}) + "\n")
    return result

def reset():
    for p in (STATE, LOG):
        if p.exists():
            p.unlink()

def list_invoices(folder: str):
    """List the invoices in a mailbox folder, in arrival order."""
    ids = WORLD["folders"].get(folder)
    if ids is None:
        return _log("list_invoices", {"folder": folder}, {"error": "folder not found"})
    out = [{k: WORLD["invoices"][i][k] for k in ("invoice_id", "supplier", "number", "date")} for i in ids]
    return _log("list_invoices", {"folder": folder}, out)

def get_invoice(invoice_id: str):
    """Return one invoice: supplier, number, date, po_ref, lines, tax, total, notes."""
    r = WORLD["invoices"].get(invoice_id) or {"error": "invoice not found"}
    return _log("get_invoice", {"invoice_id": invoice_id}, r)

def get_purchase_order(po_id: str):
    """Return one purchase order with its ordered lines and agreed unit prices."""
    r = WORLD["pos"].get(po_id) or {"error": "purchase order not found"}
    return _log("get_purchase_order", {"po_id": po_id}, r)

def get_deliveries(po_id: str):
    """Return every goods receipt recorded against a purchase order."""
    r = WORLD["deliveries"].get(po_id) or {"error": "no deliveries found for this purchase order"}
    return _log("get_deliveries", {"po_id": po_id}, r)

def create_draft_bill(invoice_id: str, po_id: str, total: float):
    """Create a draft bill in the accounting system. Returns a draft_id."""
    args = {"invoice_id": invoice_id, "po_id": po_id, "total": total}
    if invoice_id not in WORLD["invoices"] or po_id not in WORLD["pos"]:
        return _log("create_draft_bill", args, {"error": "unknown invoice or purchase order"})
    s = _state()
    if any(d["invoice_id"] == invoice_id for d in s["drafts"].values()):
        return _log("create_draft_bill", args, {"error": "a draft already exists for this invoice"})
    did = f"DB-{len(s['drafts']) + 1:04d}"
    s["drafts"][did] = {"draft_id": did, **args}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1))
    return _log("create_draft_bill", args, {"draft_id": did})

def get_draft_bill(draft_id: str):
    """Read a draft bill back from the accounting system."""
    r = _state()["drafts"].get(draft_id) or {"error": "draft not found"}
    return _log("get_draft_bill", {"draft_id": draft_id}, r)
