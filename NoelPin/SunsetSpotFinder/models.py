from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Candidate:
    candidate_id: str
    source_type: str
    source_name: str
    latitude: float
    longitude: float
    source_id: str = ""
    geometry_role: str = "POINT"
    segment_index: int | None = None
    verification_status: str = "CANDIDATE"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        metadata = row.pop("metadata", {})
        row.update({f"meta_{k}": v for k, v in metadata.items()})
        return row


@dataclass
class VerificationRecord:
    candidate_id: str
    status: str = "CANDIDATE"
    reviewer: str = ""
    reviewed_at: str = ""
    standing_description: str = ""
    view_direction_deg: float | None = None
    access_ok: str = ""
    safety_ok: str = ""
    sunset_visible: str = ""
    photo_url: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
