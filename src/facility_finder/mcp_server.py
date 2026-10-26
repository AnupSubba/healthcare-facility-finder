"""MCP server: lets Claude Desktop, IDEs and other MCP clients search the facility database.

uv run python -m facility_finder.mcp_server            # stdio transport
npx @modelcontextprotocol/inspector uv run python -m facility_finder.mcp_server
"""

from typing import Literal

from mcp.server.mcpserver import MCPServer  # MCP Python SDK 2.x (was FastMCP in 1.x)

from .models import FacilitySearch
from .repository import search

mcp = MCPServer("healthcare-facility-finder")


@mcp.tool()
def find_facilities(
    facility_type: Literal["hospital", "clinic", "lab"] | None = None,
    city: str | None = None,
    pincode: str | None = None,
    government_only: bool = False,
    emergency_only: bool = False,
    limit: int = 10,
) -> list[dict]:
    """Find hospitals, clinics or diagnostic labs in India from open public data (OpenStreetMap, data.gov.in).

    Give a city or a 6-digit pincode. Information only, not medical advice: in an emergency call 112 or 108.
    """
    f = FacilitySearch(
        intent="find",
        facility_type=facility_type,
        city=city,
        pincode=pincode,
        ownership="government" if government_only else None,
        emergency_only=emergency_only,
    )
    rows = search(f, limit=min(max(limit, 1), 25))
    keep = ("name", "type", "ownership", "address", "city", "pincode", "phone", "emergency", "lat", "lon", "updated_on")
    return [{k: r.get(k) for k in keep} for r in rows]


if __name__ == "__main__":
    mcp.run()
