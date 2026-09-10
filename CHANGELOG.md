# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-10

### Added
- CLI tool with `list`, `info`, `download`, `clean`, and `format` commands
- 5 built-in benchmarks: MMLU, GSM8K, HumanEval, TruthfulQA, BBH
- Download from Hugging Face Hub with split/config selection
- Download from local files (JSONL, JSON, CSV)
- Download from URLs (JSONL, JSON, CSV)
- Exact and fuzzy deduplication (n-gram Jaccard similarity)
- Token-based length filtering via tiktoken
- Field normalisation to `input`/`expected` schema
- JSONL export compatible with llm-eval-harness
- Push curated datasets to HF Hub
- YAML config file support (`benchmark-curator.yaml`)
- CI with GitHub Actions (Python 3.10–3.13)
- Full test suite with mocked external dependencies
