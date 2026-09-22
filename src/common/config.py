from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(config_path: str | Path) -> dict[str, Any]:
    config_path = Path(config_path).resolve()

    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    if config_path.parent.name == "configs":
        root = config_path.parent.parent
    else:
        root = config_path.parent

    path_keys = [
        "image_root",
        "labels_csv",
        "processed_root",
        "datasheet_path",
    ]

    for key in path_keys:
        value = cfg.get(key)

        if not value:
            continue

        p = Path(value)

        if p.is_absolute():
            cfg[key] = str(p)
        else:
            cfg[key] = str((root / p).resolve())

    cfg["config_path"] = str(config_path)
    cfg["project_root"] = str(root)

    return cfg


def ensure_output_dirs(cfg: dict[str, Any]) -> None:
    for key in [
        "image_root",
        "processed_root",
        "datasheet_path",
    ]:
        value = cfg.get(key)

        if not value:
            continue

        path = Path(value)

        if key == "image_root":
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)