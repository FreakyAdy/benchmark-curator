"""Tests for CLI integration."""

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from benchmark_curator.cli import app

runner = CliRunner()


class TestCLIList:
    def test_list_basic(self):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "mmlu" in result.stdout
        assert "gsm8k" in result.stdout
        assert "humaneval" in result.stdout
        assert "truthfulqa" in result.stdout
        assert "bbh" in result.stdout

    def test_list_with_details(self):
        result = runner.invoke(app, ["list", "--details"])
        assert result.exit_code == 0
        assert "HF Dataset" in result.stdout
        assert "cais/mmlu" in result.stdout


class TestCLIInfo:
    def test_info_existing(self):
        result = runner.invoke(app, ["info", "gsm8k"])
        assert result.exit_code == 0
        assert "gsm8k" in result.stdout
        assert "openai/gsm8k" in result.stdout

    def test_info_unknown(self):
        result = runner.invoke(app, ["info", "unknown"])
        assert result.exit_code != 0
        assert "Unknown benchmark" in result.stdout


class TestCLIDownload:
    @patch("benchmark_curator.cli.download_benchmark")
    def test_download_builtin(self, mock_download):
        mock_download.return_value = [{"question": "Q", "answer": "A"}] * 10

        result = runner.invoke(app, ["download", "gsm8k", "--split", "train"])
        assert result.exit_code == 0
        assert "Downloaded 10 records" in result.stdout
        mock_download.assert_called_once()

    @patch("benchmark_curator.cli.download_benchmark")
    def test_download_with_output(self, mock_download, tmp_path):
        mock_download.return_value = [{"question": "Q", "answer": "A"}]
        output_file = tmp_path / "out.jsonl"

        result = runner.invoke(app, ["download", "gsm8k", "--output", str(output_file)])
        assert result.exit_code == 0
        assert "Saved to" in result.stdout


class TestCLIClean:
    def test_clean_basic(self, tmp_path):
        input_file = tmp_path / "raw.jsonl"
        input_file.write_text('{"question": "Q1", "answer": "A1"}\n{"question": "Q2", "answer": "A2"}\n')
        output_file = tmp_path / "clean.jsonl"

        result = runner.invoke(app, ["clean", str(input_file), "--output", str(output_file)])
        assert result.exit_code == 0
        assert "Cleaned" in result.stdout
        assert output_file.exists()

    def test_clean_with_dedupe_fuzzy(self, tmp_path):
        input_file = tmp_path / "raw.jsonl"
        input_file.write_text('{"question": "What is 2+2?", "answer": "4"}\n{"question": "What is two plus two?", "answer": "four"}\n')
        output_file = tmp_path / "clean.jsonl"

        result = runner.invoke(app, [
            "clean", str(input_file), "--output", str(output_file),
            "--fuzzy", "--fuzzy-threshold", "0.8"
        ])
        assert result.exit_code == 0

    def test_clean_with_min_tokens(self, tmp_path):
        input_file = tmp_path / "raw.jsonl"
        input_file.write_text('{"question": "Hi", "answer": "A"}\n{"question": "What is the meaning of life?", "answer": "B"}\n')
        output_file = tmp_path / "clean.jsonl"

        result = runner.invoke(app, [
            "clean", str(input_file), "--output", str(output_file),
            "--min-tokens", "5"
        ])
        assert result.exit_code == 0


class TestCLIFormat:
    def test_format_basic(self, tmp_path):
        input_file = tmp_path / "clean.jsonl"
        input_file.write_text('{"input": "Q1", "expected": "A1"}\n{"input": "Q2", "expected": "A2"}\n')
        output_file = tmp_path / "eval.jsonl"

        result = runner.invoke(app, ["format", str(input_file), "--output", str(output_file)])
        assert result.exit_code == 0
        assert "Formatted 2 records" in result.stdout
        assert output_file.exists()

        # Verify output format
        lines = output_file.read_text().strip().split("\n")
        data = json.loads(lines[0])
        assert "input" in data
        assert "expected" in data

    def test_format_custom_fields(self, tmp_path):
        input_file = tmp_path / "clean.jsonl"
        input_file.write_text('{"question": "Q1", "answer": "A1"}\n')
        output_file = tmp_path / "eval.jsonl"

        result = runner.invoke(app, [
            "format", str(input_file), "--output", str(output_file),
            "--input-field", "question", "--expected-field", "answer"
        ])
        assert result.exit_code == 0


class TestCLIIntegration:
    @patch("benchmark_curator.cli.download_benchmark")
    def test_e2e_gsm8k_pipeline(self, mock_download, tmp_path):
        # Mock download to return test data AND write the output file (like real function does)
        def mock_download_side_effect(benchmark, split=None, output=None, config=None, hf_token=None):
            records = [
                {"question": "What is 2+2?", "answer": "4"},
                {"question": "What is 3+3?", "answer": "6"},
            ] * 5
            # Write to output file if specified (mimics real download_benchmark)
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                import json
                with output_path.open("w", encoding="utf-8") as f:
                    for record in records:
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
            return records

        mock_download.side_effect = mock_download_side_effect

        # Step 1: Download
        raw_file = tmp_path / "gsm8k_raw.jsonl"
        result = runner.invoke(app, ["download", "gsm8k", "--split", "train", "--output", str(raw_file)])
        assert result.exit_code == 0
        assert raw_file.exists()

        # Step 2: Clean
        clean_file = tmp_path / "gsm8k_clean.jsonl"
        result = runner.invoke(app, [
            "clean", str(raw_file), "--output", str(clean_file),
            "--dedupe", "--min-tokens", "5"
        ])
        assert result.exit_code == 0
        assert clean_file.exists()

        # Step 3: Format
        eval_file = tmp_path / "gsm8k_eval.jsonl"
        result = runner.invoke(app, [
            "format", str(clean_file), "--output", str(eval_file),
            # clean_pipeline normalizes to 'input'/'expected', so use defaults
        ])
        assert result.exit_code == 0
        assert eval_file.exists()

        # Verify final format
        lines = eval_file.read_text().strip().split("\n")
        data = json.loads(lines[0])
        assert data["input"] == "What is 2+2?"
        assert data["expected"] == "4"
