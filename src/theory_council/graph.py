"""
LangGraph state and node definitions for the Theory Council workflow.
"""
from __future__ import annotations

from typing import Any, Optional, TypedDict

from langgraph.graph import END, StateGraph

from .config import get_integrator_llm, get_llm
from .personas import (
    INTEGRATOR_SYSTEM_PROMPT,
    PROBLEM_FRAMER_PROMPT,
    SCT_AGENT_SYSTEM_PROMPT,
    SDT_AGENT_SYSTEM_PROMPT,
    WISE_AGENT_SYSTEM_PROMPT,
)


class CouncilState(TypedDict):
    """
    The shared state passed between Theory Council agents.
    """

    raw_problem: str
    framed_problem: str
    sct_output: Optional[str]
    sdt_output: Optional[str]
    wise_output: Optional[str]
    final_synthesis: Optional[str]


def problem_framer(state: CouncilState) -> CouncilState:
    """
    Normalize the raw user input into the structured format the agents expect.
    """
    llm = get_llm()
    messages = [
        {"role": "system", "content": PROBLEM_FRAMER_PROMPT},
        {"role": "user", "content": state["raw_problem"]},
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    new_state["framed_problem"] = response.content.strip()
    return new_state  # type: ignore[return-value]


def sct_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    messages = [
        {"role": "system", "content": SCT_AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Here is the structured problem description:\n\n{state['framed_problem']}",
        },
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    new_state["sct_output"] = response.content.strip()
    return new_state  # type: ignore[return-value]


def sdt_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    messages = [
        {"role": "system", "content": SDT_AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Here is the structured problem description:\n\n{state['framed_problem']}",
        },
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    new_state["sdt_output"] = response.content.strip()
    return new_state  # type: ignore[return-value]


def wise_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    messages = [
        {"role": "system", "content": WISE_AGENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Here is the structured problem description:\n\n{state['framed_problem']}",
        },
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    new_state["wise_output"] = response.content.strip()
    return new_state  # type: ignore[return-value]


def integrator(state: CouncilState) -> CouncilState:
    llm = get_integrator_llm()
    combined = (
        "=== Structured Problem ===\n"
        f"{state.get('framed_problem', '').strip()}\n\n"
        "=== SCT Agent Output ===\n"
        f"{state.get('sct_output') or ''}\n\n"
        "=== SDT Agent Output ===\n"
        f"{state.get('sdt_output') or ''}\n\n"
        "=== Wise Agent Output ===\n"
        f"{state.get('wise_output') or ''}\n"
    )
    messages = [
        {"role": "system", "content": INTEGRATOR_SYSTEM_PROMPT},
        {"role": "user", "content": combined},
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    new_state["final_synthesis"] = response.content.strip()
    return new_state  # type: ignore[return-value]


def build_graph() -> Any:
    """
    Assemble and compile the sequential Theory Council graph.
    """
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


def get_app() -> Any:
    """
    Convenience helper for callers that just need the compiled graph.
    """
    return build_graph()


__all__ = [
    "CouncilState",
    "problem_framer",
    "sct_agent",
    "sdt_agent",
    "wise_agent",
    "integrator",
    "build_graph",
    "get_app",
]


