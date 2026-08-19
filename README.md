# benchmark-curator

> Download, clean, and format LLM benchmark datasets for evaluation harnesses.

A CLI tool to fetch benchmark datasets (MMLU, GSM8K, HumanEval, TruthfulQA, BBH, etc.) from Hugging Face Hub or local sources, clean and deduplicate them, and export standardized JSONL ready for [llm-eval-harness](https://github.com/FreakyAdy/week33-llm-eval-harness) and other evaluation frameworks.

## Features

- **Download** benchmarks from HF Hub, local files, or URLs with split/config handling
- **Clean** datasets: exact/fuzzy deduplication, length filtering, field normalization
- **Format** to JSONL with `input`/`expected` schema (llm-eval-harness compatible)
- **List** available benchmarks with metadata
- **Push** curated datasets to HF Hub
- Pure Python, minimal dependencies, fully tested

## Quickstart

```bash
# Install
pip install -e .

# List available benchmarks
benchmark-curator list

# Download GSM8K (train split)
benchmark-curator download gsm8k --split train --output data/gsm8k_raw.jsonl

# Clean: dedupe, filter short samples, normalize fields
benchmark-curator clean data/gsm8k_raw.jsonl --output data/gsm8k_clean.jsonl --dedupe --min-tokens 10

# Format for llm-eval-harness (input/expected schema)
benchmark-curator format data/gsm8k_clean.jsonl --output data/gsm8k_eval.jsonl --input-field question --expected-field answer

# Run with llm-eval-harness
llm-eval run --benchmark data/gsm8k_eval.jsonl --model llama-3.1-8b-instruct-q4_k_m
```

## Installation

```bash
# From source
git clone https://github.com/FreakyAdy/week34-benchmark-curator
cd week34-benchmark-curator
pip install -e .

# Or with uv
uv pip install -e .
```

## Commands

| Command | Description |
|---------|-------------|
| `list` | Show built-in benchmarks with metadata |
| `download` | Fetch benchmark from HF Hub / local / URL |
| `clean` | Deduplicate, filter, normalize dataset |
| `format` | Export to JSONL (llm-eval-harness schema) |
| `info` | Show details for a specific benchmark |

## Built-in Benchmarks

| Name | HF Dataset | Splits | Description |
|------|------------|--------|-------------|
| `mmlu` | `cais/mmlu` | `test`, `validation`, `dev` | Massive Multitask Language Understanding |
| `gsm8k` | `openai/gsm8k` | `train`, `test` | Grade School Math 8K |
| `humaneval` | `openai/humaneval` | `test` | Code generation benchmark |
| `truthfulqa` | `truthfulqa/truthful_qa` | `validation` | Truthful QA |
| `bbh` | `lukaemon/bbh` | `test` | BIG-Bench Hard |

Additional benchmarks can be loaded from any HF dataset, local JSONL/JSON/CSV, or URL.

## Configuration

Create a `benchmark-curator.yaml` for presets:

```yaml
benchmarks:
  gsm8k:
    dataset: "openai/gsm8k"
    split: "train"
    input_field: "question"
    expected_field: "answer"
  mmlu:
    dataset: "cais/mmlu"
    config: "all"
    split: "test"
    input_field: "question"
    expected_field: "answer"
```

Then use: `benchmark-curator download gsm8k` (uses preset).

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest -q

# Lint
ruff check .
ruff format .

# Type check
mypy .
```

## License

MIT License — see [LICENSE](LICENSE) for details.