"""
Command-line interface for running the Theory Council workflow.
"""
from __future__ import annotations

from typing import Optional

import typer

from .graph import CouncilPipelineResult, run_council_pipeline

cli = typer.Typer(help="Run the Theory Council LangGraph workflow from the terminal.")


def _prompt_for_problem() -> str:
    """
    Collect a free-text problem description from stdin.
    """
    typer.echo("Describe your behavior-change or psychological intervention challenge.")
    return typer.prompt("Problem description")


@cli.command()
def run(problem: Optional[str] = typer.Option(None, "--problem", "-p", help="Problem description text.")) -> None:
    """
    Run the Theory Council workflow for the provided behavior-change problem.
    """
    text = problem or _prompt_for_problem()
    result: CouncilPipelineResult = run_council_pipeline(text)
    final_text = result.get("final_synthesis") or "(no output produced)"
    typer.echo("=== Theory Council Output ===")
    typer.echo(final_text)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()


