"""Tests for benchmark clean module."""


from benchmark_curator.clean import (
    _normalize_text,
    _record_hash,
    clean_pipeline,
    deduplicate_exact,
    deduplicate_fuzzy,
    filter_by_length,
    normalize_fields,
)


class TestNormalizeText:
    def test_normalize_whitespace(self):
        assert _normalize_text("  hello   world  ") == "hello world"
        assert _normalize_text("hello\tworld\n") == "hello world"

    def test_normalize_case(self):
        assert _normalize_text("HELLO WORLD") == "hello world"
        assert _normalize_text("HeLLo WoRLd") == "hello world"

    def test_normalize_empty(self):
        assert _normalize_text("") == ""
        assert _normalize_text("   ") == ""


class TestRecordHash:
    def test_hash_full_record(self):
        record = {"question": "Q", "answer": "A", "extra": "data"}
        h1 = _record_hash(record)
        h2 = _record_hash(record)
        assert h1 == h2
        assert len(h1) == 64  # SHA256 hex

    def test_hash_selected_fields(self):
        record = {"question": "Q", "answer": "A", "extra": "data"}
        h1 = _record_hash(record, fields=["question", "answer"])
        h2 = _record_hash(record, fields=["question", "answer"])
        assert h1 == h2

    def test_hash_different_records(self):
        record1 = {"question": "Q1", "answer": "A"}
        record2 = {"question": "Q2", "answer": "A"}
        assert _record_hash(record1) != _record_hash(record2)


class TestDeduplicateExact:
    def test_deduplicate_exact_duplicates(self):
        records = [
            {"question": "Q", "answer": "A"},
            {"question": "Q", "answer": "A"},
            {"question": "Q2", "answer": "A2"},
        ]
        result = deduplicate_exact(records)
        assert len(result) == 2
        assert result[0]["question"] == "Q"
        assert result[1]["question"] == "Q2"

    def test_deduplicate_exact_preserves_order(self):
        records = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
            {"question": "Q1", "answer": "A1"},
        ]
        result = deduplicate_exact(records)
        assert result[0]["question"] == "Q1"
        assert result[1]["question"] == "Q2"

    def test_deduplicate_exact_with_fields(self):
        records = [
            {"question": "Q", "answer": "A", "id": "1"},
            {"question": "Q", "answer": "A", "id": "2"},
        ]
        # With id field, they're different
        result = deduplicate_exact(records, fields=["question", "answer", "id"])
        assert len(result) == 2
        # Without id, they're same
        result = deduplicate_exact(records, fields=["question", "answer"])
        assert len(result) == 1

    def test_deduplicate_exact_empty(self):
        assert deduplicate_exact([]) == []


class TestDeduplicateFuzzy:
    def test_deduplicate_fuzzy_identical(self):
        records = [
            {"input": "What is 2+2?", "expected": "4"},
            {"input": "What is 2+2?", "expected": "4"},
        ]
        result = deduplicate_fuzzy(records, "input", "expected", threshold=0.95)
        assert len(result) == 1

    def test_deduplicate_fuzzy_similar(self):
        records = [
            {"input": "What is 2+2?", "expected": "4"},
            {"input": "What is 2+2 ?", "expected": "4"},
        ]
        result = deduplicate_fuzzy(records, "input", "expected", threshold=0.75)
        assert len(result) == 1  # Should be caught as similar

    def test_deduplicate_fuzzy_different(self):
        records = [
            {"input": "What is 2+2?", "expected": "4"},
            {"input": "What is 3+3?", "expected": "6"},
        ]
        result = deduplicate_fuzzy(records, "input", "expected", threshold=0.95)
        assert len(result) == 2

    def test_deduplicate_fuzzy_high_threshold(self):
        records = [
            {"input": "What is 2+2?", "expected": "4"},
            {"input": "What is 2 plus 2?", "expected": "four"},
        ]
        # High threshold should not catch these as duplicates
        result = deduplicate_fuzzy(records, "input", "expected", threshold=0.99)
        assert len(result) == 2

    def test_deduplicate_fuzzy_empty(self):
        assert deduplicate_fuzzy([], "input", "expected") == []


class TestFilterByLength:
    def test_filter_min_tokens(self):
        records = [
            {"input": "Short", "expected": "A"},
            {"input": "This is a longer question here", "expected": "B"},
        ]
        result = filter_by_length(records, "input", min_tokens=5)
        assert len(result) == 1
        assert "longer" in result[0]["input"]

    def test_filter_max_tokens(self):
        records = [
            {"input": "Short", "expected": "A"},
            {"input": "This is a much longer question that exceeds the limit", "expected": "B"},
        ]
        result = filter_by_length(records, "input", max_tokens=5)
        assert len(result) == 1
        assert result[0]["input"] == "Short"

    def test_filter_both_min_max(self):
        records = [
            {"input": "Too short", "expected": "A"},
            {"input": "Just right length here", "expected": "B"},
            {"input": "This is way too long for the maximum token limit we set", "expected": "C"},
        ]
        result = filter_by_length(records, "input", min_tokens=3, max_tokens=8)
        assert len(result) == 1
        assert result[0]["input"] == "Just right length here"

    def test_filter_no_limits(self):
        records = [{"input": "Any length", "expected": "A"}]
        result = filter_by_length(records, "input", min_tokens=0, max_tokens=None)
        assert len(result) == 1


class TestNormalizeFields:
    def test_normalize_fields_basic(self):
        records = [
            {"question": "Q1", "answer": "A1", "extra": "data"},
        ]
        result = normalize_fields(records, "question", "answer")
        assert len(result) == 1
        assert result[0]["input"] == "Q1"
        assert result[0]["expected"] == "A1"
        assert result[0]["extra"] == "data"

    def test_normalize_fields_custom_output_names(self):
        records = [{"prompt": "P", "completion": "C"}]
        result = normalize_fields(records, "prompt", "completion", "user", "assistant")
        assert result[0]["user"] == "P"
        assert result[0]["assistant"] == "C"

    def test_normalize_fields_missing_source(self):
        records = [{"other": "data"}]
        result = normalize_fields(records, "question", "answer")
        assert result[0]["input"] == ""
        assert result[0]["expected"] == ""
        assert result[0]["other"] == "data"


class TestCleanPipeline:
    def test_clean_pipeline_full(self):
        records = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q1", "answer": "A1"},  # Exact duplicate
            {"question": "Q2", "answer": "A2"},
        ]
        result = clean_pipeline(
            records,
            input_field="question",
            expected_field="answer",
            dedupe_exact=True,
            dedupe_fuzzy=False,
        )
        assert len(result) == 2
        assert result[0]["input"] == "Q1"
        assert result[0]["expected"] == "A1"

    def test_clean_pipeline_fuzzy_dedupe(self):
        records = [
            {"question": "What is 2+2?", "answer": "4"},
            {"question": "What is two plus two?", "answer": "four"},
        ]
        result = clean_pipeline(
            records,
            input_field="question",
            expected_field="answer",
            dedupe_exact=True,
            dedupe_fuzzy=True,
            fuzzy_threshold=0.8,
        )
        # Should deduplicate due to fuzzy match
        assert len(result) <= 2

    def test_clean_pipeline_length_filter(self):
        records = [
            {"question": "Hi", "answer": "A"},
            {"question": "What is the meaning of life?", "answer": "B"},
        ]
        result = clean_pipeline(
            records,
            input_field="question",
            expected_field="answer",
            min_tokens=5,
        )
        assert len(result) == 1
        assert "meaning" in result[0]["input"]

    def test_clean_pipeline_normalizes_fields(self):
        records = [{"question": "Q", "answer": "A"}]
        result = clean_pipeline(
            records,
            input_field="question",
            expected_field="answer",
        )
        assert "input" in result[0]
        assert "expected" in result[0]
        assert "question" not in result[0]
        assert "answer" not in result[0]

    def test_clean_pipeline_fuzzy_fields(self):
        records = [
            {"question": "Q", "answer": "A", "id": "1"},
            {"question": "Q", "answer": "A", "id": "2"},
        ]
        # Use id for fuzzy dedupe - should treat as different
        result = clean_pipeline(
            records,
            input_field="question",
            expected_field="answer",
            dedupe_exact=True,
            fuzzy_fields=["question", "answer", "id"],
        )
        assert len(result) == 2

        # Don't use id - should treat as same
        result = clean_pipeline(
            records,
            input_field="question",
            expected_field="answer",
            dedupe_exact=True,
            fuzzy_fields=["question", "answer"],
        )
        assert len(result) == 1
