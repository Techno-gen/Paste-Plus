from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Optional


@dataclass
class Config:
    startup_delay: float = 3.0
    wpm: int = 80
    wpm_variance: int = 15
    typo_rate: float = 0.04
    retype_rate: float = 0.02
    retype_min_chars: int = 3
    retype_max_chars: int = 12
    pause_frequency: float = 0.08
    pause_min_seconds: float = 0.4
    pause_max_seconds: float = 2.5
    posthoc_correction_rate: float = 0.15
    posthoc_max_corrections: int = 3
    fail_safe: bool = True
    inter_key_floor_ms: int = 10
    trigger_key: Optional[str] = None  # e.g. "f9" — if set, waits for this key instead of delay

    def validate(self) -> None:
        def _clamp_rate(name: str) -> None:
            val = getattr(self, name)
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name} must be between 0.0 and 1.0, got {val}")

        _clamp_rate("typo_rate")
        _clamp_rate("retype_rate")
        _clamp_rate("pause_frequency")
        _clamp_rate("posthoc_correction_rate")

        if self.wpm <= 0:
            raise ValueError(f"wpm must be positive, got {self.wpm}")
        if self.pause_min_seconds > self.pause_max_seconds:
            raise ValueError("pause_min_seconds must be <= pause_max_seconds")
        if self.retype_min_chars > self.retype_max_chars:
            raise ValueError("retype_min_chars must be <= retype_max_chars")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e


def _apply_dict(cfg: Config, data: dict[str, Any]) -> None:
    valid = {f.name for f in fields(Config)}
    for key, value in data.items():
        if key in valid:
            setattr(cfg, key, value)


def load_config(config_path: Optional[str] = None) -> Config:
    cfg = Config()

    # 1. User-global config
    user_config = Path.home() / ".paste-plus" / "config.json"
    _apply_dict(cfg, _load_json(user_config))

    # 2. Project-local config
    local_config = Path("config.json")
    _apply_dict(cfg, _load_json(local_config))

    # 3. Explicit --config path
    if config_path:
        data = _load_json(Path(config_path))
        if not data:
            raise ValueError(f"Config file not found or empty: {config_path}")
        _apply_dict(cfg, data)

    return cfg


def apply_overrides(cfg: Config, overrides: dict[str, Any]) -> None:
    """Apply CLI flag overrides (None values are skipped)."""
    _apply_dict(cfg, {k: v for k, v in overrides.items() if v is not None})
