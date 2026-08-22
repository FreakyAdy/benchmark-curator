"""Tests for benchmark registry."""

import pytest

from benchmark_curator.registry import (
    BUILTIN_BENCHMARKS,
    BenchmarkConfig,
    get_benchmark,
    list_benchmarks,
)


class TestBenchmarkConfig:
    def test_benchmark_config_creation(self):
        config = BenchmarkConfig(
            name="test",
            hf_dataset="org/dataset",
            splits=("train", "test"),
            input_field="question",
            expected_field="answer",
            config="default",
            description="Test benchmark",
            default_split="test",
        )
        assert config.name == "test"
        assert config.hf_dataset == "org/dataset"
        assert config.splits == ("train", "test")
        assert config.default_split == "test"

    def test_benchmark_config_defaults(self):
        config = BenchmarkConfig(
            name="test",
            hf_dataset="org/dataset",
            splits=("test",),
            input_field="input",
            expected_field="expected",
        )
        assert config.config is None
        assert config.description == ""
        assert config.default_split == "test"


class TestBuiltinBenchmarks:
    def test_all_benchmarks_present(self):
        expected = {"mmlu", "gsm8k", "humaneval", "truthfulqa", "bbh"}
        assert set(BUILTIN_BENCHMARKS.keys()) == expected

    def test_mmlu_config(self):
        mmlu = BUILTIN_BENCHMARKS["mmlu"]
        assert mmlu.hf_dataset == "cais/mmlu"
        assert mmlu.config == "all"
        assert mmlu.input_field == "question"
        assert mmlu.expected_field == "answer"
        assert "test" in mmlu.splits

    def test_gsm8k_config(self):
        gsm8k = BUILTIN_BENCHMARKS["gsm8k"]
        assert gsm8k.hf_dataset == "openai/gsm8k"
        assert gsm8k.config is None
        assert gsm8k.default_split == "train"

    def test_humaneval_config(self):
        humaneval = BUILTIN_BENCHMARKS["humaneval"]
        assert humaneval.hf_dataset == "openai/humaneval"
        assert humaneval.input_field == "prompt"
        assert humaneval.expected_field == "canonical_solution"

    def test_truthfulqa_config(self):
        tqa = BUILTIN_BENCHMARKS["truthfulqa"]
        assert tqa.hf_dataset == "truthfulqa/truthful_qa"
        assert tqa.config == "multiple_choice"
        assert tqa.default_split == "validation"

    def test_bbh_config(self):
        bbh = BUILTIN_BENCHMARKS["bbh"]
        assert bbh.hf_dataset == "lukaemon/bbh"
        assert bbh.input_field == "input"
        assert bbh.expected_field == "target"


class TestGetBenchmark:
    def test_get_existing_benchmark(self):
        bench = get_benchmark("mmlu")
        assert bench.name == "mmlu"

    def test_get_unknown_benchmark_raises(self):
        with pytest.raises(ValueError, match="Unknown benchmark") as exc_info:
            get_benchmark("unknown")
        assert "Unknown benchmark" in str(exc_info.value)
        assert "mmlu" in str(exc_info.value)


class TestListBenchmarks:
    def test_list_returns_all(self):
        benchmarks = list_benchmarks()
        assert len(benchmarks) == 5
        names = {b.name for b in benchmarks}
        assert names == {"mmlu", "gsm8k", "humaneval", "truthfulqa", "bbh"}
