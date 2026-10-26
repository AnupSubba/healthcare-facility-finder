"""Pydantic models shared by the agent, the API and the MCP server."""

from typing import Literal

from pydantic import BaseModel, Field

FacilityType = Literal["hospital", "clinic", "lab"]


class FacilitySearch(BaseModel):
    """What the LLM extracts from a question. Code, not the LLM, turns this into SQL."""

    intent: Literal["find", "explain", "emergency", "out_of_scope"] = Field(
        description="find = looking for a facility; explain = asking what a term means; "
        "emergency = urgent medical situation; out_of_scope = medical advice or anything else"
    )
    facility_type: FacilityType | None = Field(default=None, description="hospital, clinic or lab (diagnostic lab)")
    city: str | None = Field(default=None, description="City or town in English, e.g. Lucknow, Bengaluru")
    pincode: str | None = Field(default=None, pattern=r"^[1-9][0-9]{5}$", description="6-digit Indian pincode")
    near_me: bool = Field(default=False, description="User said near me / nearby / paas / aas-paas")
    ownership: Literal["government", "private"] | None = Field(
        default=None, description="government (sarkari) or private; leave empty if not mentioned"
    )
    emergency_only: bool = Field(default=False, description="User wants emergency / casualty services")
    name_contains: str | None = Field(default=None, description="Part of a facility name if the user named one")
    radius_km: float = Field(default=5, ge=0.5, le=50)
    language: Literal["en", "hi"] = Field(default="en", description="hi if the user wrote in Hindi or Hinglish")
