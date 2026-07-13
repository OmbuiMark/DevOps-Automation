from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


class InputError(Exception):
    """Raised when input YAML is missing or malformed."""


def load_component_yaml(path: str | Path) -> Dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise InputError(f"Input file not found: {file_path}")

    try:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise InputError(f"Invalid YAML: {exc}") from exc

    if not isinstance(data, dict) or "component" not in data:
        raise InputError("YAML must contain a top-level 'component' object")

    component = data["component"]
    if not isinstance(component, dict):
        raise InputError("'component' must be a mapping/object")

    return component
