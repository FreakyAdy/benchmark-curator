"""Tests for benchmark format module."""

import json
from unittest.mock import MagicMock, patch

from benchmark_curator.format import (
    export_jsonl,
    load_jsonl,
    push_to_hub,
)


class TestExportJsonl:
    def test_export_jsonl_basic(self, tmp_path):
        records = [
            {"input": "Q1", "expected": "A1"},
            {"input": "Q2", "expected": "A2"},
        ]
        output_file = tmp_path / "output.jsonl"
        count = export_jsonl(records, str(output_file))

        assert count == 2
        assert output_file.exists()
        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["input"] == "Q1"
        assert json.loads(lines[0])["expected"] == "A1"

    def test_export_jsonl_with_metadata(self, tmp_path):
        records = [
            {"input": "Q1", "expected": "A1", "category": "math", "difficulty": "easy"},
        ]
        output_file = tmp_path / "output.jsonl"
        count = export_jsonl(records, str(output_file))

        assert count == 1
        data = json.loads(output_file.read_text())
        assert data["input"] == "Q1"
        assert data["expected"] == "A1"
        assert data["category"] == "math"
        assert data["difficulty"] == "easy"

    def test_export_jsonl_custom_field_names(self, tmp_path):
        records = [
            {"question": "Q1", "answer": "A1"},
        ]
        output_file = tmp_path / "output.jsonl"
        count = export_jsonl(records, str(output_file), input_field="question", expected_field="answer")

        assert count == 1
        data = json.loads(output_file.read_text())
        assert data["input"] == "Q1"
        assert data["expected"] == "A1"

    def test_export_jsonl_skips_missing_fields(self, tmp_path):
        records = [
            {"input": "Q1", "expected": "A1"},
            {"input": "Q2"},  # missing expected
            {"expected": "A3"},  # missing input
        ]
        output_file = tmp_path / "output.jsonl"
        count = export_jsonl(records, str(output_file))

        assert count == 1  # Only first record has both fields

    def test_export_jsonl_creates_parent_dirs(self, tmp_path):
        records = [{"input": "Q", "expected": "A"}]
        output_file = tmp_path / "nested" / "dir" / "output.jsonl"
        count = export_jsonl(records, str(output_file))

        assert count == 1
        assert output_file.exists()

    def test_export_jsonl_empty_records(self, tmp_path):
        output_file = tmp_path / "output.jsonl"
        count = export_jsonl([], str(output_file))
        assert count == 0
        assert output_file.exists()
        assert output_file.read_text() == ""


class TestLoadJsonl:
    def test_load_jsonl_basic(self, tmp_path):
        file_path = tmp_path / "input.jsonl"
        file_path.write_text('{"input": "Q1", "expected": "A1"}\n{"input": "Q2", "expected": "A2"}\n')

        records = load_jsonl(str(file_path))
        assert len(records) == 2
        assert records[0]["input"] == "Q1"
        assert records[1]["expected"] == "A2"

    def test_load_jsonl_skips_empty_lines(self, tmp_path):
        file_path = tmp_path / "input.jsonl"
        file_path.write_text('{"input": "Q1"}\n\n{"input": "Q2"}\n   \n{"input": "Q3"}')

        records = load_jsonl(str(file_path))
        assert len(records) == 3

    def test_load_jsonl_empty_file(self, tmp_path):
        file_path = tmp_path / "input.jsonl"
        file_path.write_text("")

        records = load_jsonl(str(file_path))
        assert records == []


class TestPushToHub:
    @patch("datasets.Dataset")
    @patch("benchmark_curator.format.HfApi")
    def test_push_to_hub(self, mock_hf_api, mock_dataset):
        mock_ds_instance = MagicMock()
        mock_dataset.from_list.return_value = mock_ds_instance

        mock_api_instance = MagicMock()
        mock_hf_api.return_value = mock_api_instance

        records = [{"input": "Q1", "expected": "A1"}]
        url = push_to_hub(records, "user/dataset", split="train", private=True)

        mock_dataset.from_list.assert_called_once_with(records)
        mock_ds_instance.push_to_hub.assert_called_once_with(
            "user/dataset", split="train", token=None, private=True
        )
        assert url == "https://huggingface.co/datasets/user/dataset"
