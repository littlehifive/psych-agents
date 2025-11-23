# Theory Council (LangGraph Demo)

Local Python demo of a "Theory Council" that routes a behavior-change or health promotion problem description through multiple theory-inspired agents and synthesizes the results with Intervention Mapping (IM) structure. Everything runs in the terminal using LangGraph, LangChain, and OpenAI models.

## Features
- Problem-framing helper that converts raw text into an IM-friendly brief.
- IM Anchor agent that drafts a logic model of the problem & change (Steps 1-2).
- Five theory agents (SCT, SDT, Wise/Belonging, Reasoned Action, Environment & Implementation) that map determinants, methods, and applications into IM Step 2-3 language.
- Debate Moderator plus Theory Selector that critique, rank, and prioritize the most relevant theory lenses.
- Integrator agent that produces a final Intervention Mapping-ready synthesis (Steps 1-3 with implementation notes).
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

The CLI now guides users through four concise sections:
1. Raw problem text plus the AI framing sent to agents.
2. Debate highlights (including Theory Selector rationale).
3. Intervention Mapping guidance grounded in prioritized theories.
4. Recommended intervention concept(s) derived from the IM blueprint.

## LangSmith / LangChain Tracing
- Set `LANGCHAIN_TRACING_V2=true` in `.env`.
- Provide `LANGCHAIN_API_KEY`, optional `LANGCHAIN_ENDPOINT`, and `LANGCHAIN_PROJECT` (defaults to `theory-council`).

## Extending the System
- Add new persona prompts in `src/theory_council/personas.py`.
- Introduce more agents by defining new nodes in `src/theory_council/graph.py` and wiring them into the `StateGraph`.
- Adjust CLI formatting or expose additional options in `src/theory_council/cli.py`.

## Requirements
- Python 3.11+
- OpenAI API access for GPT-4o-mini (agents) and GPT-4.1 (integrator by default).

This demo is intended for local experimentation—feel free to adapt prompts, nodes, or orchestration logic for your own psychological intervention explorations.