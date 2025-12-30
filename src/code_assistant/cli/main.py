"""CLI interface for Code Assistant."""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from code_assistant.services import CodeAnalyzer, CodeIndexer

console = Console()


def run_async(coro):
    """Run async function from sync context."""
    return asyncio.get_event_loop().run_until_complete(coro)


@click.group()
@click.version_option(version="0.1.0", prog_name="code-assistant")
def cli():
    """Code Assistant - LLM-powered code understanding and debugging."""
    pass


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    default=["__pycache__", ".git", ".venv", "venv", "node_modules"],
    help="Patterns to exclude",
)
def index(directory: str, exclude: tuple[str, ...]):
    """Index a codebase directory for analysis."""
    indexer = CodeIndexer()

    console.print(f"[blue]Indexing directory: {directory}[/blue]")

    try:
        result = indexer.index_directory(
            Path(directory),
            list(exclude) if exclude else None,
        )

        # Display results
        table = Table(title="Indexing Complete")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Directory", result["directory"])
        table.add_row("Files Indexed", str(result["files_indexed"]))
        table.add_row("Total Chunks", str(result["total_chunks"]))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("target")
def explain(target: str):
    """Explain a function or class."""
    analyzer = CodeAnalyzer()

    console.print(f"[blue]Explaining: {target}[/blue]\n")

    try:
        result = run_async(analyzer.explain(target))
        console.print(Panel(
            result["explanation"],
            title=f"[bold]Explanation: {target}[/bold]",
            border_style="green",
        ))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command("debug")
@click.argument("file_path", type=click.Path(exists=True))
def debug_file(file_path: str):
    """Analyze a file for bugs and issues."""
    analyzer = CodeAnalyzer()

    console.print(f"[blue]Analyzing: {file_path}[/blue]\n")

    try:
        result = run_async(analyzer.debug(file_path))
        console.print(Panel(
            result["report"],
            title=f"[bold]Bug Analysis: {file_path}[/bold]",
            border_style="red",
        ))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("target")
def refactor(target: str):
    """Get refactoring suggestions for code."""
    analyzer = CodeAnalyzer()

    console.print(f"[blue]Analyzing for refactoring: {target}[/blue]\n")

    try:
        result = run_async(analyzer.refactor(target))
        console.print(Panel(
            result["suggestions"],
            title=f"[bold]Refactoring Suggestions[/bold]",
            border_style="yellow",
        ))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command("generate-tests")
@click.argument("target")
def generate_tests(target: str):
    """Generate test cases for a function or class."""
    analyzer = CodeAnalyzer()

    console.print(f"[blue]Generating tests for: {target}[/blue]\n")

    try:
        result = run_async(analyzer.generate_tests(target))

        # Display as syntax-highlighted code
        console.print(Panel(
            Syntax(result["tests"], "python", theme="monokai"),
            title=f"[bold]Generated Tests: {target}[/bold]",
            border_style="cyan",
        ))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--type", "-t", "chunk_type", help="Filter by type: function, class, method")
@click.option("--limit", "-n", default=10, help="Number of results")
def search(query: str, chunk_type: str | None, limit: int):
    """Search the indexed codebase."""
    indexer = CodeIndexer()

    console.print(f"[blue]Searching for: {query}[/blue]\n")

    results = indexer.search(query, limit, chunk_type)

    if not results:
        console.print("[yellow]No results found[/yellow]")
        return

    for i, result in enumerate(results, 1):
        meta = result.get("metadata", {})
        content = result.get("content", "")[:300]

        console.print(Panel(
            f"[dim]File: {meta.get('file_path', 'unknown')}[/dim]\n"
            f"[dim]Lines: {meta.get('start_line', '?')}-{meta.get('end_line', '?')}[/dim]\n\n"
            f"{content}{'...' if len(result.get('content', '')) > 300 else ''}",
            title=f"[bold]{i}. {meta.get('qualified_name', 'unknown')}[/bold] ({meta.get('chunk_type', 'code')})",
            border_style="blue",
        ))


@cli.command()
def chat():
    """Start an interactive chat session."""
    analyzer = CodeAnalyzer()

    console.print(Panel(
        "Welcome to Code Assistant Chat!\n"
        "Ask questions about your codebase. Type 'exit' or 'quit' to leave.",
        title="[bold]Code Assistant[/bold]",
        border_style="green",
    ))

    history: list[tuple[str, str]] = []

    while True:
        try:
            user_input = console.input("\n[bold blue]You:[/bold blue] ")

            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[yellow]Goodbye![/yellow]")
                break

            if not user_input.strip():
                continue

            with console.status("[bold green]Thinking...[/bold green]"):
                response = run_async(analyzer.chat(user_input, history))

            console.print(f"\n[bold green]Assistant:[/bold green] {response}")

            # Update history
            history.append((user_input, response))

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", "-p", default=8000, help="Port to bind")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the API server."""
    import uvicorn

    console.print(f"[green]Starting server at http://{host}:{port}[/green]")
    uvicorn.run(
        "code_assistant.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    cli()
