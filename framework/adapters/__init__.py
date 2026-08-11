"""Telemetry adapters that map repo signals into run-record fields."""

from __future__ import annotations

from .github_diff import opacity_from_diff_stats
from .inspect_repo import inspect_repository

__all__ = ["inspect_repository", "opacity_from_diff_stats"]
