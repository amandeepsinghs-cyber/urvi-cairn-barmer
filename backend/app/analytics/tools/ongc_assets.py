"""Backward-compatible re-export of Cairn Oil & Gas (Vedanta Limited) India assets."""
from __future__ import annotations

from .cairn_assets import SOURCE_NOTE, _ASSETS, _tags, cairn_assets

ongc_assets = cairn_assets

__all__ = ["SOURCE_NOTE", "_ASSETS", "_tags", "cairn_assets", "ongc_assets"]
