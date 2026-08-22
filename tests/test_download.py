"""Tests for benchmark download module."""

from unittest.mock import MagicMock, patch

import pytest

from benchmark_curator.download import (
    download_benchmark,
    download_from_file,
    download_from_url,
)
from benchmark_curator.registry import BenchmarkConfig


class TestDownloadBenchmark:
    @patch("benchmark_curator.download.load_dataset")
    def test_download_benchmark_from_hf(self, mock_load_dataset):
        mock_ds = MagicMock()
        mock_ds.to_list.return_value = [
            {"question": "What is 2+2?", "answer": "4"},
            {"question": "What is 3+3?", "answer": "6"},
        ]
        mock_load_dataset.return_value = mock_ds

        bench_config = BenchmarkConfig(
            name="test",
            hf_dataset="org/test",
            splits=("test",),
            input_field="question",
            expected_field="answer",
            default_split="test",
        )

        records = download_benchmark(bench_config, split="test")
        assert len(records) == 2
        assert records[0]["question"] == "What is 2+2?"
        mock_load_dataset.assert_called_once_with("org/test", name=None, split="test", token=None)

    @patch("benchmark_curator.download.load_dataset")
    def test_download_benchmark_with_config(self, mock_load_dataset):
        mock_ds = MagicMock()
        mock_ds.to_list.return_value = [{"input": "test", "target": "out"}]
        mock_load_dataset.return_value = mock_ds

        bench_config = BenchmarkConfig(
            name="test",
            hf_dataset="org/test",
            splits=("test",),
            input_field="input",
            expected_field="target",
            config="my_config",
            default_split="test",
        )
        download_benchmark(bench_config, config="my_config")
        mock_load_dataset.assert_called_once_with(
            "org/test", name="my_config", split="test", token=None
        )

    @patch("benchmark_curator.download.load_dataset")
    def test_download_benchmark_invalid_split(self, mock_load_dataset):
        bench_config = BenchmarkConfig(
            name="test",
            hf_dataset="org/test",
            splits=("test",),
            input_field="input",
            expected_field="target",
            default_split="test",
        )

        with pytest.raises(ValueError, match="not available") as exc_info:
            download_benchmark(bench_config, split="invalid")
        assert "not available" in str(exc_info.value)

    @patch("benchmark_curator.download.load_dataset")
    def test_download_benchmark_saves_output(self, mock_load_dataset, tmp_path):
        mock_ds = MagicMock()
        mock_ds.to_list.return_value = [{"question": "Q", "answer": "A"}]
        mock_load_dataset.return_value = mock_ds

        bench_config = BenchmarkConfig(
            name="test",
            hf_dataset="org/test",
            splits=("test",),
            input_field="question",
            expected_field="answer",
            default_split="test",
        )

        output_file = tmp_path / "output.jsonl"
        download_benchmark(bench_config, output=str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "question" in content
        assert "answer" in content


class TestDownloadFromFile:
    def test_download_from_jsonl(self, tmp_path):
        file_path = tmp_path / "test.jsonl"
        file_path.write_text(
            '{"question": "Q1", "answer": "A1"}\n{"question": "Q2", "answer": "A2"}\n'
        )

        records = download_from_file(str(file_path), "question", "answer")
        assert len(records) == 2
        assert records[0]["question"] == "Q1"

    def test_download_from_json(self, tmp_path):
        file_path = tmp_path / "test.json"
        file_path.write_text('[{"question": "Q1", "answer": "A1"}]')

        records = download_from_file(str(file_path), "question", "answer")
        assert len(records) == 1
        assert records[0]["question"] == "Q1"

    def test_download_from_csv(self, tmp_path):
        file_path = tmp_path / "test.csv"
        file_path.write_text("question,answer\nQ1,A1\nQ2,A2\n")

        records = download_from_file(str(file_path), "question", "answer")
        assert len(records) == 2
        assert records[0]["question"] == "Q1"

    def test_download_from_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            download_from_file("/nonexistent/file.jsonl", "q", "a")

    def test_download_from_unsupported_format_raises(self, tmp_path):
        file_path = tmp_path / "test.txt"
        file_path.write_text("plain text")

        with pytest.raises(ValueError, match="Unsupported file format") as exc_info:
            download_from_file(str(file_path), "q", "a")
        assert "Unsupported file format" in str(exc_info.value)


class TestDownloadFromUrl:
    @patch("urllib.request.urlopen")
    def test_download_from_jsonl_url(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = (
            b'{"question": "Q1", "answer": "A1"}\n{"question": "Q2", "answer": "A2"}'
        )
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        records = download_from_url("http://example.com/data.jsonl", "question", "answer")
        assert len(records) == 2

    @patch("urllib.request.urlopen")
    def test_download_from_json_url(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b'[{"question": "Q1", "answer": "A1"}]'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        records = download_from_url("http://example.com/data.json", "question", "answer")
        assert len(records) == 1

    @patch("urllib.request.urlopen")
    def test_download_from_csv_url(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"question,answer\nQ1,A1\nQ2,A2"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        records = download_from_url("http://example.com/data.csv", "question", "answer")
        assert len(records) == 2

    def test_download_from_invalid_extension_raises(self):
        with pytest.raises(ValueError, match="URL must end with") as exc_info:
            download_from_url("http://example.com/data.txt", "q", "a")
        assert "URL must end with" in str(exc_info.value)

    @patch("urllib.request.urlopen")
    def test_download_from_url_http_error(self, mock_urlopen):
        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            "http://example.com/data.jsonl", 404, "Not Found", {}, None
        )
        with pytest.raises(urllib.error.HTTPError):
            download_from_url("http://example.com/data.jsonl", "q", "a")
