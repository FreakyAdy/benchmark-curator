"""Download benchmarks from Hugging Face Hub, local files, or URLs."""

import json
from pathlib import Path

from datasets import load_dataset

from .registry import BenchmarkConfig, get_benchmark


def download_benchmark(
    benchmark: str | BenchmarkConfig,
    split: str | None = None,
    output: str | None = None,
    config: str | None = None,
    hf_token: str | None = None,
) -> list[dict]:
    """
    Download a benchmark dataset and return as list of dicts.
    
    Args:
        benchmark: Benchmark name (str) or BenchmarkConfig
        split: Dataset split to download (overrides default)
        output: Optional path to save raw JSONL
        config: Dataset config name (for multi-config datasets)
        hf_token: Optional HF token for private datasets
    
    Returns:
        List of dataset records as dicts
    """
    if isinstance(benchmark, str):
        bench_config = get_benchmark(benchmark)
    else:
        bench_config = benchmark

    # Resolve split
    split = split or bench_config.default_split
    if split not in bench_config.splits:
        raise ValueError(f"Split '{split}' not available for {bench_config.name}. Available: {bench_config.splits}")

    # Resolve config
    config = config or bench_config.config

    # Load from HF Hub
    ds = load_dataset(
        bench_config.hf_dataset,
        name=config,
        split=split,
        token=hf_token,
    )

    records = ds.to_list()

    # Save to output if requested
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return records


def download_from_file(
    path: str,
    input_field: str,
    expected_field: str,
) -> list[dict]:
    """
    Load benchmark from a local file (JSONL, JSON, or CSV).
    
    Args:
        path: Path to local file
        input_field: Field name for input/prompt
        expected_field: Field name for expected output
    
    Returns:
        List of normalized records
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path_obj.suffix.lower()

    if suffix == ".jsonl":
        records = []
        with path_obj.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    elif suffix == ".json":
        with path_obj.open("r", encoding="utf-8") as f:
            data = json.load(f)
            records = data if isinstance(data, list) else [data]
    elif suffix == ".csv":
        import csv
        records = []
        with path_obj.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .jsonl, .json, or .csv")

    return records


def download_from_url(
    url: str,
    input_field: str,
    expected_field: str,
) -> list[dict]:
    """
    Download benchmark from a URL (JSONL, JSON, or CSV).

    Args:
        url: URL to download from
        input_field: Field name for input/prompt
        expected_field: Field name for expected output

    Returns:
        List of normalized records
    """
    import urllib.request

    # Check extension first (before network call)
    if not (url.endswith(".jsonl") or url.endswith(".json") or url.endswith(".csv")):
        raise ValueError("URL must end with .jsonl, .json, or .csv")

    with urllib.request.urlopen(url) as response:
        content = response.read().decode("utf-8")

    if url.endswith(".jsonl"):
        records = []
        for line in content.strip().split("\n"):
            if line:
                records.append(json.loads(line))
    elif url.endswith(".json"):
        data = json.loads(content)
        records = data if isinstance(data, list) else [data]
    elif url.endswith(".csv"):
        import csv
        import io
        records = []
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            records.append(row)

    return records
