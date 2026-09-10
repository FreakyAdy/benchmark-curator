"""YAML configuration file support for benchmark-curator."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class BenchmarkPreset:
    """A benchmark preset loaded from a config file."""

    dataset: str | None = None
    split: str | None = None
    config: str | None = None
    input_field: str | None = None
    expected_field: str | None = None


def find_config_file(start_dir: str | Path | None = None) -> Path | None:
    """
    Search for a benchmark-curator.yaml config file.

    Searches the given directory and its parents, returning the first match.

    Args:
        start_dir: Directory to start searching from (default: CWD)

    Returns:
        Path to config file, or None if not found
    """
    if start_dir is None:
        start_dir = Path.cwd()
    else:
        start_dir = Path(start_dir)

    config_names = ["benchmark-curator.yaml", "benchmark-curator.yml"]

    current = start_dir.resolve()
    while True:
        for name in config_names:
            candidate = current / name
            if candidate.is_file():
                return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def load_config(path: str | Path | None = None) -> dict[str, BenchmarkPreset]:
    """
    Load benchmark presets from a YAML config file.

    Args:
        path: Explicit path to config file, or None to auto-discover

    Returns:
        Dict mapping benchmark names to BenchmarkPreset objects.
        Returns empty dict if no config file is found.
    """
    if path is None:
        config_path = find_config_file()
    else:
        config_path = Path(path)

    if config_path is None or not config_path.is_file():
        return {}

    with config_path.open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    benchmarks_raw = raw.get("benchmarks", {})
    if not isinstance(benchmarks_raw, dict):
        return {}

    presets: dict[str, BenchmarkPreset] = {}
    for name, values in benchmarks_raw.items():
        if not isinstance(values, dict):
            continue
        presets[str(name)] = BenchmarkPreset(
            dataset=values.get("dataset"),
            split=values.get("split"),
            config=values.get("config"),
            input_field=values.get("input_field"),
            expected_field=values.get("expected_field"),
        )

    return presets
