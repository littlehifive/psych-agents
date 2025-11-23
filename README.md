# Theory Council (LangGraph Demo)

Local Python demo of a "Theory Council" that routes a behavior-change problem description through several theory-inspired agents (Social Cognitive Theory, Self-Determination Theory, Wise Intervention) and then synthesizes the outputs via an Integrator agent. Everything runs in the terminal using LangGraph, LangChain, and OpenAI models.

## Features
- Problem-framing helper that turns raw text into a structured brief.
- Three persona-driven agents grounded in major behavior-change theories.
- Integrator agent that weaves agent proposals into 2–3 intervention packages.
- Simple Typer-based CLI (`python -m theory_council.cli`).
- Optional LangSmith/LangChain tracing hooks.

## Project Structure
```
theory-council/
  .gitignore
  .env.example
  requirements.txt
  README.md
  src/
    theory_council/
      config.py
      personas.py
      graph.py
      cli.py
```

## Getting Started
1. **Create & activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment**
   ```bash
   cp .env.example .env
   # edit .env to add OPENAI_API_KEY and optional LangSmith vars
   ```

## Running the CLI
```bash
python -m theory_council.cli
# or provide text inline
python -m theory_council.cli --problem "Students feel disconnected from first-year STEM courses..."
```

The CLI prints:
1. Structured problem brief
2. SCT agent proposals
3. SDT agent proposals
4. Wise intervention proposals
5. Final synthesized intervention packages

## LangSmith / LangChain Tracing
- Set `LANGCHAIN_TRACING_V2=true` in `.env`.
- Provide `LANGCHAIN_API_KEY`, optional `LANGCHAIN_ENDPOINT`, and `LANGCHAIN_PROJECT` (defaults to `theory-council`).

## Extending the System
- Add new persona prompts in `src/theory_council/personas.py`.
- Introduce more agents by defining new nodes in `src/theory_council/graph.py` and wiring them into the `StateGraph`.
- Adjust CLI formatting or expose additional options in `src/theory_council/cli.py`.

## Requirements
- Python 3.11+
- OpenAI API access for GPT-4.1-mini (changeable in `config.py`).

This demo is intended for local experimentation—feel free to adapt prompts, nodes, or orchestration logic for your own psychological intervention explorations.