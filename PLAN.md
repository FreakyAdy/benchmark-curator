# Week 34 Benchmark Curator — Execution Plan

> **Goal:** Deliver a complete, tested CLI tool (`benchmark-curator`) for downloading, cleaning, and formatting LLM benchmark datasets to JSONL (llm-eval-harness compatible). One public repo: `FreakyAdy/week34-benchmark-curator`.
>
> **Parallel PR Target:** inspect_ai #4770 — `ChatMessage.text` setter preserves content block order when content is `list[Content]`.

---

## Milestones (Tue–Sat)

| Day | Focus | Deliverables (DoD) |
|-----|-------|---------------------|
| **Tue (Day 2)** | Core: Registry + Download | • `registry.py`: 6 built-in benchmarks (MMLU, GSM8K, HumanEval, TruthfulQA, BBH) ✓<br>• `download.py`: HF Hub (split/config), local file (JSONL/JSON/CSV), URL fallback ✓<br>• Unit tests: `test_registry.py`, `test_download.py` (mocked HF)<br>• `ruff check .` + `ruff format .` clean |
| **Wed (Day 3)** | Core: Clean + Format | • `clean.py`: exact/fuzzy dedupe, length filter, field normalization ✓<br>• `format.py`: JSONL export (input/expected schema), HF Hub push ✓<br>• Unit tests: `test_clean.py`, `test_format.py`<br>• Full test suite green |
| **Thu (Day 4)** | CLI Polish + Integration | • `cli.py`: Typer + Rich — `list`, `download`, `clean`, `format`, `info` commands<br>• Config file support (YAML presets)<br>• E2E test: download GSM8K → clean → format → verify loads in llm-eval-harness<br>• Full test suite + lint green |
| **Fri (Day 5)** | Docs + Examples + PR #4770 Start | • Comprehensive README with quickstart, command reference, examples<br>• Example: download GSM8K + HumanEval → clean → format → run with llm-eval-harness<br>• Inspect_ai: explore codebase, understand `ChatMessage.text` setter bug, run baseline |
| **Sat (Day 6)** | PR #4770 Implementation + Finalize | • Fix `ChatMessage.text` setter (preserve block order)<br>• Add tests asserting order preservation<br>• Full inspect_ai test suite + lint<br>• Open PR `Fixes #4770` (claim issue first per CONTRIBUTING)<br>• Final benchmark-curator test + lint, push fixes<br>• Update PROJECT_STATE.md |

---

## Definition of Done (per task)

- **Code**: Implements spec, typed, documented
- **Tests**: Unit + integration where applicable, mocks for external deps (HF Hub)
- **Quality**: `ruff check .` + `ruff format .` + `mypy .` clean
- **CI**: GitHub Actions passes on Python 3.10–3.13
- **Commit**: One coherent change, descriptive message

---

## Acceptance Criteria (Project)

1. `benchmark-curator list` shows 6 built-in benchmarks with metadata
2. `benchmark-curator download gsm8k --split train` fetches from HF Hub
3. `benchmark-curator clean data/raw.jsonl --dedupe --min-tokens 10` dedupes + filters
4. `benchmark-curator format data/clean.jsonl --output data/eval.jsonl` produces valid llm-eval-harness JSONL
5. E2E: curated GSM8K + HumanEval run successfully in `llm-eval-harness`
6. All tests pass locally and in CI (4 Python versions)
7. PR #4770 submitted to inspect_ai with tests green

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| HF Hub rate limits / network flakes | Mock all HF calls in tests; use `hf_hub_download` with local cache |
| `datasets` / `tiktoken` version conflicts | Pin in pyproject.toml; test on 4 Python versions |
| inspect_ai #4770 blocked by maintainers | Claim issue early; submit PR even if review delayed (completion = PR submitted + tests green) |

---

## Tracking

- Repo: `FreakyAdy/week34-benchmark-curator` (public)
- Issue: "week-plan" linking this file
- PR Target: `UKGovernmentBEIS/inspect_ai#4770`
- Daily commits: ≥1 Mon–Sat (no zero-commit days)