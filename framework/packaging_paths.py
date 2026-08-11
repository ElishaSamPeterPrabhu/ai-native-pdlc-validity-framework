"""Resolve bundled framework assets when installed from PyPI or run from source."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def framework_dir() -> Path:
    """Directory containing schemas, templates, and catalog files."""
    return Path(files("framework"))


def bundled_path(*parts: str) -> Path:
    return framework_dir().joinpath(*parts)
