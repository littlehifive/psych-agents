# AGENTS.md — Instructions for the Coding Assistant

You are an AI coding assistant helping build a LOCAL Python demo of a multi-agent "Theory Council" using **LangGraph + LangChain + OpenAI**.

The goal is:

- A small Python project where a user describes a **behavior-change / psychological intervention problem**.
- A LangGraph workflow routes this problem through several **theory-inspired agents**:
  - Social Cognitive Theory (Bandura-inspired) agent.
  - Self-Determination Theory (Deci & Ryan-inspired) agent.
  - Wise Intervention / Belonging (Walton-inspired) agent.
- Each agent generates theory-based intervention ideas.
- An **Integrator agent** synthesizes the proposals into 2–3 concrete intervention packages with mechanisms.
- Everything runs locally via CLI (no web UI needed for v1), with **optional** tracing/logging to **LangSmith**.

The user will **not** be providing PDFs or an external knowledge base. You should rely on the OpenAI model’s internal knowledge and well-crafted prompts (persona cards) to shape each agent.

---

## 0. Project structure

Create a minimal project with this structure:

```text
theory-council/
  .gitignore
  .env.example        # template; .env will be git-ignored
  pyproject.toml      # or requirements.txt (see below)
  README.md

  src/
    __init__.py
    theory_council/
      __init__.py
      config.py       # env loading, LLM client constructors
      personas.py     # persona definitions / prompts for each agent
      graph.py        # LangGraph state + nodes + compiled app
      cli.py          # command-line runner to interact with the graph


If you prefer requirements.txt over pyproject.toml, that is acceptable. Do one dependency management approach, not both.

1. Dependencies & environment
1.1. Dependencies

Use Python 3.11+ if available.

Install (via pyproject.toml or requirements.txt):

langgraph

langchain

langchain-openai

python-dotenv

(optional) typer or click for CLI ergonomics
If adding a CLI lib feels heavy, a simple input()-based CLI is fine.

Example requirements.txt (if using that):

langgraph>=0.2.0
langchain>=0.3.0
langchain-openai>=0.3.0
python-dotenv>=1.0.1
typer>=0.12.0

1.2. Environment variables

The project must support:

OPENAI_API_KEY # required

LANGCHAIN_TRACING_V2 # optional (true/false)

LANGCHAIN_API_KEY # optional for LangSmith

LANGCHAIN_ENDPOINT # default: https://api.smith.langchain.com

LANGCHAIN_PROJECT # e.g., "theory-council"

The user will manage these in a local .env file, and that file will be git-ignored. You should create a .env.example with placeholders; the user will copy it to .env and fill in real keys.

Use python-dotenv in config.py to load .env automatically.

2. config.py — environment + LLM clients

Create src/theory_council/config.py with:

A function to load environment variables (using dotenv.load_dotenv()).

A function get_llm() returning a ChatOpenAI (or ChatOpenAI-compatible) instance with:

default model: "gpt-4.1-mini" or "gpt-4o-mini" (or similar, but keep it as a constant).

sensible temperature (e.g., 0.3–0.5) because we want thoughtful, consistent output.

Optionally a separate get_integration_llm() if you want a different temperature or model for the Integrator agent.

Example behavior (pseudocode, not exact code):

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

load_dotenv()

def get_llm(model: str = "gpt-4.1-mini", temperature: float = 0.3) -> ChatOpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return ChatOpenAI(model=model, temperature=temperature)


Make sure the module reads .env automatically when imported.

3. personas.py — theory-inspired persona cards

Create src/theory_council/personas.py.

Define three persona prompt strings (or small dataclasses) that encode how each agent should behave. These are inspired by the theorists, not impersonating them.

Each persona should:

State its theoretical lens.

List key constructs.

Explain how it reasons about behavior change.

Give guidelines for intervention ideas (what to propose, what to avoid).

Explicitly avoid claiming to be the real person or to represent them.

Example: Social Cognitive Theory agent persona (as a Python string constant):

SCT_AGENT_SYSTEM_PROMPT = """
You are the Social Cognitive Theory Agent, inspired by the work of Albert Bandura.
You are NOT Albert Bandura and you do not speak in the first person as him.
You reason from social cognitive theory and the self-efficacy literature.

Your job:
- Take a structured problem description about a behavior-change challenge.
- Re-express it in social cognitive terms.
- Identify key determinants and mechanisms: self-efficacy, observational learning, outcome expectancies, environmental facilitators/barriers, self-regulation, etc.
- Propose 3–5 feasible intervention ideas that are explicitly grounded in these mechanisms.
- For each idea, explain:
  - which SCT constructs it targets,
  - why it should work in this context,
  - key risks or boundary conditions (e.g., risk of undermining agency or autonomy).

Be concise but specific. Avoid generic advice. Do not invent empirical results; instead, speak at the level of theory-informed reasoning.
"""


Similarly, define:

SDT_AGENT_SYSTEM_PROMPT (Self-Determination Theory — autonomy, competence, relatedness).

WISE_AGENT_SYSTEM_PROMPT (Wise interventions / belonging — attributions, meaning-making, social norms, subtle reframing).

Also define a system prompt for an Integrator agent, e.g.:

INTEGRATOR_SYSTEM_PROMPT = """
You are the Integrator Agent for a 'Theory Council' of psychological intervention designers.
You have received proposals from several theory-inspired agents (e.g., SCT, SDT, Wise Intervention).

Your job:
- Read and compare their proposals.
- Identify overlapping ideas and complementary strengths.
- Synthesize 2–3 concrete intervention packages that:
  - are clearly described (who, what, when, how),
  - explicitly map to underlying mechanisms from multiple theories,
  - highlight how they might promote human agency rather than undermine it.
- For each package, provide:
  - a short title,
  - a description,
  - mechanisms and theoretical justification,
  - key risks or open questions for human researchers to examine.

Write in a clear, structured format that a researcher or practitioner could use as a starting point.
"""

4. graph.py — LangGraph state + nodes

Create src/theory_council/graph.py with:

A state definition using TypedDict or pydantic for clarity. Example:

from typing import TypedDict, List, Optional

class CouncilState(TypedDict):
    raw_problem: str
    framed_problem: str
    sct_output: Optional[str]
    sdt_output: Optional[str]
    wise_output: Optional[str]
    final_synthesis: Optional[str]


Node functions for:

problem_framer

sct_agent

sdt_agent

wise_agent

integrator

Each node function:

Accepts a CouncilState.

Uses get_llm() from config.py.

Sends a structured prompt: system prompt (from personas.py) + user content containing the relevant part of the state.

Returns an updated state (copy of previous dict + new fields).

Example pattern (not exact code, but shape):

from langgraph.graph import StateGraph, END
from .config import get_llm
from .personas import (
    SCT_AGENT_SYSTEM_PROMPT,
    SDT_AGENT_SYSTEM_PROMPT,
    WISE_AGENT_SYSTEM_PROMPT,
    INTEGRATOR_SYSTEM_PROMPT,
)

def problem_framer(state: CouncilState) -> CouncilState:
    llm = get_llm()
    prompt = (
        "You are a problem-framing assistant for psychological interventions.\n"
        "Take the raw description below and convert it into a structured summary with:\n"
        "- Population and setting\n"
        "- Target behavior(s)\n"
        "- Barriers and assets\n"
        "- Delivery channel (if known)\n"
        "- Constraints and goals\n\n"
        f"Raw description:\n{state['raw_problem']}\n"
    )
    resp = llm.invoke(prompt)
    new_state = dict(state)
    new_state["framed_problem"] = resp.content
    return new_state


For an agent node, you must use the system prompt + the framed problem:

def sct_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    messages = [
        {"role": "system", "content": SCT_AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Here is the structured problem description:\n\n{state['framed_problem']}",
        },
    ]
    resp = llm.invoke(messages)
    new_state = dict(state)
    new_state["sct_output"] = resp.content
    return new_state


Graph wiring:

Use StateGraph from langgraph.graph. The flow should be:

Entry: problem_framer

Then: sct_agent, sdt_agent, wise_agent — you can chain them sequentially for simplicity, or run them in parallel if you want.

Finally: integrator creates final_synthesis and returns.

Simple sequential wiring:

from langgraph.graph import StateGraph, END

def build_graph():
    graph = StateGraph(CouncilState)

    graph.add_node("problem_framer", problem_framer)
    graph.add_node("sct_agent", sct_agent)
    graph.add_node("sdt_agent", sdt_agent)
    graph.add_node("wise_agent", wise_agent)
    graph.add_node("integrator", integrator)

    graph.set_entry_point("problem_framer")
    graph.add_edge("problem_framer", "sct_agent")
    graph.add_edge("sct_agent", "sdt_agent")
    graph.add_edge("sdt_agent", "wise_agent")
    graph.add_edge("wise_agent", "integrator")
    graph.add_edge("integrator", END)

    return graph.compile()


The integrator node should read sct_output, sdt_output, and wise_output, then use the INTEGRATOR_SYSTEM_PROMPT to synthesize a final_synthesis string.

Example shape:

def integrator(state: CouncilState) -> CouncilState:
    llm = get_llm(temperature=0.4)
    combined = (
        "=== SCT Agent Output ===\n" + (state.get("sct_output") or "") + "\n\n"
        "=== SDT Agent Output ===\n" + (state.get("sdt_output") or "") + "\n\n"
        "=== Wise Agent Output ===\n" + (state.get("wise_output") or "") + "\n"
    )
    messages = [
        {"role": "system", "content": INTEGRATOR_SYSTEM_PROMPT},
        {"role": "user", "content": combined},
    ]
    resp = llm.invoke(messages)
    new_state = dict(state)
    new_state["final_synthesis"] = resp.content
    return new_state


Export a get_app() or similar function that returns the compiled graph:

def get_app():
    return build_graph()

5. cli.py — simple command-line interface

Create src/theory_council/cli.py that:

Imports get_app() from graph.py.

Prompts the user (via input() or Typer) for a free-text problem description.

Creates an initial CouncilState:

initial_state = {
    "raw_problem": user_input,
    "framed_problem": "",
    "sct_output": None,
    "sdt_output": None,
    "wise_output": None,
    "final_synthesis": None,
}


Runs the graph:

app = get_app()
result = app.invoke(initial_state)


Prints out:

The framed problem.

Each theory agent’s output.

The final synthesis.

Format nicely:

print("=== Structured Problem ===")
print(result["framed_problem"])
print("\n=== SCT Agent ===")
print(result["sct_output"])
print("\n=== SDT Agent ===")
print(result["sdt_output"])
print("\n=== Wise Intervention Agent ===")
print(result["wise_output"])
print("\n=== Final Synthesized Intervention Packages ===")
print(result["final_synthesis"])


Optionally expose an entry point in if __name__ == "__main__": so the user can run:

python -m theory_council.cli

6. README.md

Generate a simple README.md that explains:

What the project does (Theory Council multi-agent demo).

How to set up:

python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# edit .env to add API keys
python -m theory_council.cli


How to enable LangSmith tracing by setting LANGCHAIN_TRACING_V2=true and filling LANGCHAIN_API_KEY, LANGCHAIN_PROJECT.

7. Style & quality guidelines

When writing code:

Use clear function names and docstrings.

Keep prompts in one place (personas.py) so they are easy to iterate on.

Handle missing environment variables gracefully (raise clear errors).

Prefer type hints (e.g., -> CouncilState) where practical.

Assume the user may later extend the system with more theory agents or a debate loop, so keep the graph wiring readable.

Do NOT:

Attempt to scrape PDFs or external data.

Hard-code any real API keys.

Commit .env file; only .env.example should be tracked.

Focus on making the project runnable end-to-end and easy for the user to modify prompts and add new theory agents later.