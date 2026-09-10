"""CLI for benchmark-curator."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .clean import clean_pipeline
from .config import load_config
from .download import download_benchmark, download_from_file, download_from_url
from .format import export_jsonl, load_jsonl, push_to_hub
from .registry import get_benchmark, list_benchmarks

app = typer.Typer(
    name="benchmark-curator",
    help="Download, clean, and format LLM benchmark datasets for evaluation harnesses.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

console = Console()


def _save_records(records: list[dict], output: str) -> None:
    """Save records to a JSONL file."""
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


@app.command("list")
def list_command(
    show_details: bool = typer.Option(False, "--details", "-d", help="Show detailed metadata"),
) -> None:
    """List all built-in benchmarks."""
    benchmarks = list_benchmarks()

    if show_details:
        for bench in benchmarks:
            console.print(f"\n[bold cyan]{bench.name}[/bold cyan]")
            console.print(f"  HF Dataset: {bench.hf_dataset}")
            console.print(f"  Config: {bench.config or 'N/A'}")
            console.print(f"  Splits: {', '.join(bench.splits)}")
            console.print(f"  Default Split: {bench.default_split}")
            console.print(f"  Input Field: {bench.input_field}")
            console.print(f"  Expected Field: {bench.expected_field}")
            console.print(f"  Description: {bench.description}")
    else:
        table = Table(title="Built-in Benchmarks")
        table.add_column("Name", style="cyan")
        table.add_column("HF Dataset", style="green")
        table.add_column("Splits", style="yellow")
        table.add_column("Input Field", style="magenta")
        table.add_column("Expected Field", style="magenta")
        table.add_column("Description", style="white")

        for bench in benchmarks:
            table.add_row(
                bench.name,
                bench.hf_dataset,
                ", ".join(bench.splits),
                bench.input_field,
                bench.expected_field,
                bench.description,
            )
        console.print(table)


@app.command()
def info(
    benchmark: str = typer.Argument(..., help="Benchmark name"),
) -> None:
    """Show detailed info for a specific benchmark."""
    try:
        bench = get_benchmark(benchmark)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

    console.print(f"\n[bold cyan]{bench.name}[/bold cyan]")
    console.print(f"  HF Dataset: {bench.hf_dataset}")
    console.print(f"  Config: {bench.config or 'N/A'}")
    console.print(f"  Splits: {', '.join(bench.splits)}")
    console.print(f"  Default Split: {bench.default_split}")
    console.print(f"  Input Field: {bench.input_field}")
    console.print(f"  Expected Field: {bench.expected_field}")
    console.print(f"  Description: {bench.description}")


@app.command()
def download(
    benchmark: str = typer.Argument(
        ..., help="Benchmark name (built-in), or local file path, or URL"
    ),
    split: str | None = typer.Option(
        None, "--split", "-s", help="Dataset split (overrides default)"
    ),
    output: str | None = typer.Option(None, "--output", "-o", help="Output JSONL file path"),
    config: str | None = typer.Option(
        None, "--config", "-c", help="Dataset config (for multi-config datasets)"
    ),
    hf_token: str | None = typer.Option(None, "--hf-token", help="HF token for private datasets"),
    input_field: str | None = typer.Option(
        None, "--input-field", help="Input field name (for file/url sources)"
    ),
    expected_field: str | None = typer.Option(
        None, "--expected-field", help="Expected field name (for file/url sources)"
    ),
) -> None:
    """Download a benchmark dataset from HF Hub, local file, or URL."""
    # Detect if benchmark is a local file path
    if Path(benchmark).exists():
        if not input_field or not expected_field:
            console.print(
                "[red]Error: --input-field and --expected-field required for file download[/red]"
            )
            raise typer.Exit(1)
        console.print(f"Loading from file [cyan]{benchmark}[/cyan]...")
        try:
            records = download_from_file(benchmark, input_field, expected_field)
            console.print(f"[green]✓ Loaded {len(records)} records from file[/green]")
            if output:
                _save_records(records, output)
                console.print(f"  Saved to: {output}")
        except Exception as e:
            console.print(f"[red]Error loading file: {e}[/red]")
            raise typer.Exit(1) from None
        return

    # Detect if benchmark is a URL
    if benchmark.startswith(("http://", "https://")):
        if not input_field or not expected_field:
            console.print(
                "[red]Error: --input-field and --expected-field required for URL download[/red]"
            )
            raise typer.Exit(1)
        console.print(f"Downloading from URL [cyan]{benchmark}[/cyan]...")
        try:
            records = download_from_url(benchmark, input_field, expected_field)
            console.print(f"[green]✓ Downloaded {len(records)} records from URL[/green]")
            if output:
                _save_records(records, output)
                console.print(f"  Saved to: {output}")
        except Exception as e:
            console.print(f"[red]Error downloading from URL: {e}[/red]")
            raise typer.Exit(1) from None
        return

    # Built-in benchmark
    try:
        bench_config = get_benchmark(benchmark)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from None

    # Apply YAML config presets (CLI args take precedence)
    presets = load_config()
    preset = presets.get(benchmark)
    if preset:
        split = split or preset.split
        config = config or preset.config

    resolved_split = split or bench_config.default_split
    resolved_config = config or bench_config.config

    console.print(
        f"Downloading [cyan]{bench_config.name}[/cyan] "
        f"(split: {resolved_split}, config: {resolved_config})..."
    )

    try:
        records = download_benchmark(
            bench_config,
            split=resolved_split,
            output=output,
            config=resolved_config,
            hf_token=hf_token,
        )
        console.print(f"[green]✓ Downloaded {len(records)} records[/green]")
        if output:
            console.print(f"  Saved to: {output}")
    except Exception as e:
        console.print(f"[red]Error downloading: {e}[/red]")
        raise typer.Exit(1) from None


@app.command()
def clean(
    input_file: str = typer.Argument(..., help="Input JSONL file"),
    output: str = typer.Option(..., "--output", "-o", help="Output JSONL file"),
    input_field: str = typer.Option("question", "--input-field", help="Input field name"),
    expected_field: str = typer.Option("answer", "--expected-field", help="Expected field name"),
    dedupe_exact: bool = typer.Option(
        True, "--dedupe/--no-dedupe", help="Enable exact deduplication"
    ),
    dedupe_fuzzy: bool = typer.Option(
        False, "--fuzzy/--no-fuzzy", help="Enable fuzzy deduplication"
    ),
    fuzzy_threshold: float = typer.Option(
        0.95, "--fuzzy-threshold", help="Fuzzy similarity threshold (0-1)"
    ),
    min_tokens: int = typer.Option(0, "--min-tokens", help="Minimum token count"),
    max_tokens: int | None = typer.Option(None, "--max-tokens", help="Maximum token count"),
) -> None:
    """Clean and transform a benchmark dataset."""
    console.print(f"Loading [cyan]{input_file}[/cyan]...")
    records = load_jsonl(input_file)
    console.print(f"Loaded {len(records)} records")

    console.print("Running clean pipeline...")
    cleaned = clean_pipeline(
        records,
        input_field=input_field,
        expected_field=expected_field,
        dedupe_exact=dedupe_exact,
        dedupe_fuzzy=dedupe_fuzzy,
        fuzzy_threshold=fuzzy_threshold,
        min_tokens=min_tokens,
        max_tokens=max_tokens,
    )

    console.print(f"[green]✓ Cleaned: {len(records)} → {len(cleaned)} records[/green]")

    console.print(f"Saving to [cyan]{output}[/cyan]...")
    count = export_jsonl(cleaned, output)
    console.print(f"[green]✓ Saved {count} records[/green]")


@app.command()
def format(
    input_file: str = typer.Argument(..., help="Input JSONL file (cleaned)"),
    output: str = typer.Option(..., "--output", "-o", help="Output JSONL file"),
    input_field: str = typer.Option(
        "input", "--input-field", help="Input field name (default: input)"
    ),
    expected_field: str = typer.Option(
        "expected", "--expected-field", help="Expected field name (default: expected)"
    ),
    push: bool = typer.Option(False, "--push", help="Push to HF Hub after formatting"),
    repo_id: str | None = typer.Option(
        None, "--repo-id", help="HF Hub repo ID (e.g., user/dataset)"
    ),
    split: str = typer.Option("train", "--split", help="Dataset split name"),
    private: bool = typer.Option(False, "--private", help="Create private HF repo"),
) -> None:
    """Format cleaned dataset to llm-eval-harness JSONL schema."""
    console.print(f"Loading [cyan]{input_file}[/cyan]...")
    records = load_jsonl(input_file)
    console.print(f"Loaded {len(records)} records")

    console.print("Formatting to llm-eval-harness schema...")
    count = export_jsonl(records, output, input_field=input_field, expected_field=expected_field)
    console.print(f"[green]✓ Formatted {count} records → {output}[/green]")

    if push:
        if not repo_id:
            console.print("[red]Error: --repo-id required for --push[/red]")
            raise typer.Exit(1)
        console.print(f"Pushing to HF Hub: {repo_id}...")
        url = push_to_hub(records, repo_id, split=split, private=private)
        console.print(f"[green]✓ Pushed: {url}[/green]")


if __name__ == "__main__":
    app()
