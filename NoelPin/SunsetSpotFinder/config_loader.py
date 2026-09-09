from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as fp:
        config = yaml.safe_load(fp) or {}
    config["_config_path"] = str(path.resolve())
    config["_root"] = str(path.resolve().parent.parent)
    return config


def resolve_path(config: dict[str, Any], raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return Path(config["_root"]) / path
