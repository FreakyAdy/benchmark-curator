"""Format and export benchmark datasets."""

import json
from pathlib import Path
from typing import Optional

from huggingface_hub import HfApi


def export_jsonl(
    records: list[dict],
    output: str,
    input_field: str = "input",
    expected_field: str = "expected",
) -> int:
    """
    Export records to JSONL format.
    
    Args:
        records: List of records with input/expected fields
        output: Output file path
        input_field: Field name for input (default: "input")
        expected_field: Field name for expected output (default: "expected")
    
    Returns:
        Number of records written
    """
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    count = 0
    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            # Ensure required fields exist
            if input_field not in record or expected_field not in record:
                continue
            out_record = {
                "input": record[input_field],
                "expected": record[expected_field],
            }
            # Include any additional metadata fields
            for k, v in record.items():
                if k not in (input_field, expected_field):
                    out_record[k] = v
            f.write(json.dumps(out_record, ensure_ascii=False) + "\n")
            count += 1
    
    return count


def push_to_hub(
    records: list[dict],
    repo_id: str,
    split: str = "train",
    token: Optional[str] = None,
    private: bool = False,
) -> str:
    """
    Push records to Hugging Face Hub as a dataset.
    
    Args:
        records: List of records to push
        repo_id: HF Hub repository ID (e.g., "username/dataset-name")
        split: Dataset split name
        token: HF token (or None to use cached)
        private: Whether to create private repo
    
    Returns:
        URL of the created dataset
    """
    from datasets import Dataset
    
    ds = Dataset.from_list(records)
    ds.push_to_hub(repo_id, split=split, token=token, private=private)
    
    api = HfApi()
    return f"https://huggingface.co/datasets/{repo_id}"


def load_jsonl(path: str) -> list[dict]:
    """Load records from a JSONL file."""
    records = []
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records