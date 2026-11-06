"""MCP server that gives Hermes the fake invoice tools. Needs: pip install "mcp<2"  (v2 renamed FastMCP, so pin v1)
Run by Hermes over stdio; you register it in Hermes' MCP config (see README)."""
from mcp.server.fastmcp import FastMCP
import world_api as W
mcp = FastMCP("invoice-mock")
for fn in (W.list_invoices, W.get_invoice, W.get_purchase_order, W.get_deliveries,
           W.create_draft_bill, W.get_draft_bill):
    mcp.tool()(fn)
if __name__ == "__main__":
    mcp.run()
