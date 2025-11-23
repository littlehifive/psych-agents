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


def _run_council(problem: str) -> CouncilState:
    """
    Execute the Theory Council graph for the provided problem statement.
    """
    initial_state: CouncilState = {
        "raw_problem": problem,
        "im_summary": None,
        "theory_outputs": {},
        "debate_summary": None,
        "theory_ranking": None,
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
    final_text = (result.get("final_synthesis") or "").strip() or "(no output produced)"
    typer.echo("=== Theory Council Output ===")
    typer.echo(final_text)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()


