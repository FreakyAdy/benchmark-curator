"""Benchmark registry with built-in benchmark definitions."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration for a benchmark dataset."""

    name: str
    hf_dataset: str
    splits: tuple[str, ...]
    input_field: str
    expected_field: str
    config: str | None = None
    description: str = ""
    default_split: str = field(default="test")


# Built-in benchmark definitions
BUILTIN_BENCHMARKS: dict[str, BenchmarkConfig] = {
    "mmlu": BenchmarkConfig(
        name="mmlu",
        hf_dataset="cais/mmlu",
        splits=("test", "validation", "dev"),
        input_field="question",
        expected_field="answer",
        config="all",
        description="Massive Multitask Language Understanding",
        default_split="test",
    ),
    "gsm8k": BenchmarkConfig(
        name="gsm8k",
        hf_dataset="openai/gsm8k",
        splits=("train", "test"),
        input_field="question",
        expected_field="answer",
        description="Grade School Math 8K",
        default_split="train",
    ),
    "humaneval": BenchmarkConfig(
        name="humaneval",
        hf_dataset="openai/humaneval",
        splits=("test",),
        input_field="prompt",
        expected_field="canonical_solution",
        description="Code generation benchmark",
        default_split="test",
    ),
    "truthfulqa": BenchmarkConfig(
        name="truthfulqa",
        hf_dataset="truthfulqa/truthful_qa",
        splits=("validation",),
        input_field="question",
        expected_field="best_answer",
        config="multiple_choice",
        description="Truthful QA",
        default_split="validation",
    ),
    "bbh": BenchmarkConfig(
        name="bbh",
        hf_dataset="lukaemon/bbh",
        splits=("test",),
        input_field="input",
        expected_field="target",
        description="BIG-Bench Hard",
        default_split="test",
    ),
}


def get_benchmark(name: str) -> BenchmarkConfig:
    """Get a built-in benchmark configuration by name."""
    if name not in BUILTIN_BENCHMARKS:
        raise ValueError(f"Unknown benchmark: {name}. Available: {list(BUILTIN_BENCHMARKS.keys())}")
    return BUILTIN_BENCHMARKS[name]


def list_benchmarks() -> list[BenchmarkConfig]:
    """List all built-in benchmark configurations."""
    return list(BUILTIN_BENCHMARKS.values())
