"""Tests for YAML config file support."""

import textwrap

from benchmark_curator.config import (
    BenchmarkPreset,
    find_config_file,
    load_config,
)


class TestFindConfigFile:
    def test_find_config_in_cwd(self, tmp_path):
        config_file = tmp_path / "benchmark-curator.yaml"
        config_file.write_text("benchmarks: {}")
        result = find_config_file(tmp_path)
        assert result == config_file

    def test_find_yml_extension(self, tmp_path):
        config_file = tmp_path / "benchmark-curator.yml"
        config_file.write_text("benchmarks: {}")
        result = find_config_file(tmp_path)
        assert result == config_file

    def test_find_config_in_parent(self, tmp_path):
        config_file = tmp_path / "benchmark-curator.yaml"
        config_file.write_text("benchmarks: {}")
        child = tmp_path / "subdir"
        child.mkdir()
        result = find_config_file(child)
        assert result == config_file

    def test_no_config_found(self, tmp_path):
        child = tmp_path / "empty_dir"
        child.mkdir()
        result = find_config_file(child)
        assert result is None


class TestLoadConfig:
    def test_load_valid_config(self, tmp_path):
        config_file = tmp_path / "benchmark-curator.yaml"
        config_file.write_text(
            textwrap.dedent("""\
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
            """)
        )
        presets = load_config(str(config_file))
        assert "gsm8k" in presets
        assert "mmlu" in presets
        assert presets["gsm8k"].dataset == "openai/gsm8k"
        assert presets["gsm8k"].split == "train"
        assert presets["gsm8k"].input_field == "question"
        assert presets["gsm8k"].expected_field == "answer"
        assert presets["mmlu"].config == "all"

    def test_load_empty_config(self, tmp_path):
        config_file = tmp_path / "benchmark-curator.yaml"
        config_file.write_text("")
        presets = load_config(str(config_file))
        assert presets == {}

    def test_load_missing_file(self, tmp_path):
        presets = load_config(str(tmp_path / "nonexistent.yaml"))
        assert presets == {}

    def test_load_partial_preset(self, tmp_path):
        config_file = tmp_path / "benchmark-curator.yaml"
        config_file.write_text(
            textwrap.dedent("""\
            benchmarks:
              custom:
                dataset: "org/custom"
            """)
        )
        presets = load_config(str(config_file))
        assert "custom" in presets
        assert presets["custom"].dataset == "org/custom"
        assert presets["custom"].split is None
        assert presets["custom"].config is None

    def test_benchmark_preset_defaults(self):
        preset = BenchmarkPreset()
        assert preset.dataset is None
        assert preset.split is None
        assert preset.config is None
        assert preset.input_field is None
        assert preset.expected_field is None
