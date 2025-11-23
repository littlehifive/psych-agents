"""
Command-line interface for running the Theory Council workflow.
"""
from __future__ import annotations

from typing import Optional

import typer

from .graph import CouncilState, get_app

cli = typer.Typer(help="Run the Theory Council LangGraph workflow from the terminal.")


def _prompt_for_problem() -> str:
    """
    Collect a free-text problem description from stdin.
    """
    typer.echo("Describe your behavior-change or psychological intervention challenge.")
    return typer.prompt("Problem description")


def _format_section(title: str, body: Optional[str]) -> str:
    """
    Produce a simple textual section for CLI output.
    """
    divider = "=" * len(title)
    content = body or "(no output)"
    return f"{divider}\n{title}\n{divider}\n{content.strip()}\n"


def _run_council(problem: str) -> CouncilState:
    """
    Execute the Theory Council graph for the provided problem statement.
    """
    initial_state: CouncilState = {
        "raw_problem": problem,
        "framed_problem": "",
        "sct_output": None,
        "sdt_output": None,
        "wise_output": None,
        "final_synthesis": None,
    }
    app = get_app()
    return app.invoke(initial_state)


@cli.command()
def run(problem: Optional[str] = typer.Option(None, "--problem", "-p", help="Problem description text.")) -> None:
    """
    Run the Theory Council workflow for the provided behavior-change problem.
    """
    text = problem or _prompt_for_problem()
    result = _run_council(text)

    sections = [
        _format_section("Structured Problem", result.get("framed_problem")),
        _format_section("SCT Agent", result.get("sct_output")),
        _format_section("SDT Agent", result.get("sdt_output")),
        _format_section("Wise Intervention Agent", result.get("wise_output")),
        _format_section("Final Synthesized Intervention Packages", result.get("final_synthesis")),
    ]

    for section in sections:
        typer.echo(section)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()


