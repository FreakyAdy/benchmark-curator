"""Clean and transform benchmark datasets."""

import hashlib
import json

import tiktoken


def _normalize_text(text: str) -> str:
    """Normalize text for comparison."""
    return " ".join(text.strip().lower().split())


def _record_hash(record: dict, fields: list[str] | None = None) -> str:
    """Compute hash of a record for deduplication."""
    if fields:
        content = "".join(str(record.get(f, "")) for f in fields)
    else:
        content = json.dumps(record, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(content.encode()).hexdigest()


def deduplicate_exact(
    records: list[dict],
    fields: list[str] | None = None,
) -> list[dict]:
    """
    Remove exact duplicates from records.

    Args:
        records: List of records
        fields: Optional fields to use for deduplication (default: all fields)

    Returns:
        Deduplicated records (preserves first occurrence order)
    """
    seen = set()
    result = []
    for record in records:
        h = _record_hash(record, fields)
        if h not in seen:
            seen.add(h)
            result.append(record)
    return result


def deduplicate_fuzzy(
    records: list[dict],
    input_field: str,
    expected_field: str,
    threshold: float = 0.95,
) -> list[dict]:
    """
    Remove fuzzy duplicates based on text similarity.

    Uses a simple n-gram Jaccard similarity on normalized text.

    Args:
        records: List of records
        input_field: Field containing input text
        expected_field: Field containing expected output
        threshold: Similarity threshold (0-1), higher = more aggressive

    Returns:
        Deduplicated records
    """

    def get_ngrams(text: str, n: int = 3) -> set[str]:
        text = _normalize_text(text)
        return {text[i : i + n] for i in range(len(text) - n + 1)}

    def jaccard(a: set[str], b: set[str]) -> float:
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return len(a & b) / len(a | b)

    result = []
    signatures: list[tuple[set[str], set[str]]] = []  # List of (input_ngrams, expected_ngrams)

    for record in records:
        input_text = str(record.get(input_field, ""))
        expected_text = str(record.get(expected_field, ""))

        input_ngrams = get_ngrams(input_text)
        expected_ngrams = get_ngrams(expected_text)

        is_duplicate = False
        for sig_in, sig_exp in signatures:
            sim_in = jaccard(input_ngrams, sig_in)
            sim_exp = jaccard(expected_ngrams, sig_exp)
            if sim_in >= threshold and sim_exp >= threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            result.append(record)
            signatures.append((input_ngrams, expected_ngrams))

    return result


def filter_by_length(
    records: list[dict],
    input_field: str,
    min_tokens: int = 0,
    max_tokens: int | None = None,
    encoding: str = "cl100k_base",
) -> list[dict]:
    """
    Filter records by token length of input field.

    Args:
        records: List of records
        input_field: Field containing input text
        min_tokens: Minimum token count (inclusive)
        max_tokens: Maximum token count (inclusive), None = no limit
        encoding: tiktoken encoding name

    Returns:
        Filtered records
    """
    enc = tiktoken.get_encoding(encoding)

    result = []
    for record in records:
        text = str(record.get(input_field, ""))
        token_count = len(enc.encode(text))
        if token_count >= min_tokens and (max_tokens is None or token_count <= max_tokens):
            result.append(record)
    return result


def normalize_fields(
    records: list[dict],
    input_field: str,
    expected_field: str,
    output_input_field: str = "input",
    output_expected_field: str = "expected",
) -> list[dict]:
    """
    Normalize record fields to standard input/expected schema.

    Args:
        records: List of records
        input_field: Source field for input
        expected_field: Source field for expected output
        output_input_field: Target field name for input
        output_expected_field: Target field name for expected output

    Returns:
        Records with normalized fields
    """
    result = []
    for record in records:
        new_record = {k: v for k, v in record.items() if k not in (input_field, expected_field)}
        new_record[output_input_field] = record.get(input_field, "")
        new_record[output_expected_field] = record.get(expected_field, "")
        result.append(new_record)
    return result


def clean_pipeline(
    records: list[dict],
    input_field: str,
    expected_field: str,
    dedupe_exact: bool = True,
    dedupe_fuzzy: bool = False,
    fuzzy_threshold: float = 0.95,
    min_tokens: int = 0,
    max_tokens: int | None = None,
    fuzzy_fields: list[str] | None = None,
) -> list[dict]:
    """
    Run the full cleaning pipeline on records.

    Args:
        records: Input records
        input_field: Input field name
        expected_field: Expected field name
        dedupe_exact: Enable exact deduplication
        dedupe_fuzzy: Enable fuzzy deduplication
        fuzzy_threshold: Fuzzy similarity threshold
        min_tokens: Minimum token length
        max_tokens: Maximum token length
        fuzzy_fields: Fields to use for fuzzy dedupe (default: input+expected)

    Returns:
        Cleaned records
    """
    # Exact deduplication first
    if dedupe_exact:
        records = deduplicate_exact(records, fields=fuzzy_fields)

    # Fuzzy deduplication
    if dedupe_fuzzy:
        records = deduplicate_fuzzy(records, input_field, expected_field, fuzzy_threshold)

    # Length filtering
    if min_tokens > 0 or max_tokens is not None:
        records = filter_by_length(records, input_field, min_tokens, max_tokens)

    # Normalize fields
    records = normalize_fields(records, input_field, expected_field)

    return records
