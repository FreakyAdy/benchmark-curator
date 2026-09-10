# Contributing to benchmark-curator

Thanks for considering contributing! Here's how to get set up and what we expect.

## Development Setup

**Requirements:** Python ≥ 3.10

```bash
# Clone
git clone https://github.com/FreakyAdy/benchmark-curator.git
cd benchmark-curator

# Install with dev dependencies (using pip)
pip install -e ".[dev]"

# Or using uv
uv pip install -e ".[dev]"
```

## Running Tests

```bash
# Run the full test suite
pytest -q

# Run with coverage
pytest --cov=src/benchmark_curator --cov-report=term-missing

# Run a specific test file
pytest tests/test_clean.py -v
```

## Linting & Formatting

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check lint
ruff check .

# Auto-fix lint issues
ruff check . --fix

# Check formatting
ruff format --check .

# Auto-format
ruff format .
```

## Type Checking

```bash
mypy .
```

## Code Style

- All functions must have type annotations and docstrings
- Use `ruff check` + `ruff format` before committing (CI enforces this)
- Tests should mock external calls (HF Hub, network) — no live API calls in tests

## Adding a Built-in Benchmark

1. Add a `BenchmarkConfig` entry to `BUILTIN_BENCHMARKS` in [`src/benchmark_curator/registry.py`](src/benchmark_curator/registry.py)
2. Add corresponding tests in [`tests/test_registry.py`](tests/test_registry.py)
3. Update the README benchmark table

## Pull Requests

1. Fork the repo and create a branch from `main`
2. Make your changes in small, focused commits
3. Add or update tests for any new functionality
4. Ensure `pytest`, `ruff check .`, `ruff format --check .` all pass
5. Open a PR with a clear description of what you changed and why

## Issues

- **Bug reports:** Include Python version, OS, the command you ran, and the full error traceback
- **Feature requests:** Describe the use case, not just the solution

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
