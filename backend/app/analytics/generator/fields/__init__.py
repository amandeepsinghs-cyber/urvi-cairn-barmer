"""FIELD_CONFIGS registry and well-ID prefix resolution for Cairn Barmer Basin (RJ-ON-90/1)."""

from __future__ import annotations

from .aishwariya import AISHWARIYA
from .base import (
    ClusterConfig,
    DowntimeModel,
    FacilityConfig,
    FieldConfig,
    FixtureSpec,
    ReservoirRanges,
)
from .bhagyam import BHAGYAM
from .mangala import MANGALA
from .raageshwari import RAAGESHWARI

FIELD_CONFIGS: dict[str, FieldConfig] = {
    "Mangala": MANGALA,
    "Bhagyam": BHAGYAM,
    "Aishwariya": AISHWARIYA,
    "Raageshwari": RAAGESHWARI,
}

# Longest prefix first so prefixes never shadow each other.
_PREFIXES = sorted(((c.prefix, c.field) for c in FIELD_CONFIGS.values()), key=lambda t: -len(t[0]))


def field_of(well_id: str) -> str | None:
    """Return the field for a well ID by prefix, or None if the prefix is unknown."""
    wid = (well_id or "").upper()
    for prefix, field in _PREFIXES:
        if wid.startswith(prefix):
            return field
    return None


def resolve_field(name: str) -> str | None:
    """Case-insensitive field-name lookup."""
    for f in FIELD_CONFIGS:
        if f.lower() == (name or "").lower():
            return f
    return None


__all__ = [
    "AISHWARIYA",
    "BHAGYAM",
    "FIELD_CONFIGS",
    "MANGALA",
    "RAAGESHWARI",
    "ClusterConfig",
    "DowntimeModel",
    "FacilityConfig",
    "FieldConfig",
    "FixtureSpec",
    "ReservoirRanges",
    "field_of",
    "resolve_field",
]
