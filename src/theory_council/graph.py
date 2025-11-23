"""
LangGraph state and node definitions for the Theory Council workflow.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import END, StateGraph

from .config import get_integrator_llm, get_llm
from .personas import (
    DEBATE_MODERATOR_SYSTEM_PROMPT,
    ENV_IMPL_AGENT_SYSTEM_PROMPT,
    IM_ANCHOR_SYSTEM_PROMPT,
    INTEGRATOR_SYSTEM_PROMPT,
    RA_AGENT_SYSTEM_PROMPT,
    SCT_AGENT_SYSTEM_PROMPT,
    SDT_AGENT_SYSTEM_PROMPT,
    THEORY_SELECTOR_SYSTEM_PROMPT,
    WISE_AGENT_SYSTEM_PROMPT,
)

THEORY_LABELS = [
    ("sct", "SCT (Social Cognitive Theory)"),
    ("sdt", "SDT (Self-Determination Theory)"),
    ("wise", "Wise / Belonging"),
    ("ra", "Reasoned Action / Decision"),
    ("env_impl", "Environment and Implementation"),
]


class CouncilState(TypedDict):
    """
    The shared state passed between Theory Council agents.
    """

    raw_problem: str
    im_summary: Optional[str]
    theory_outputs: Dict[str, str]
    debate_summary: Optional[str]
    theory_ranking: Optional[str]
    final_synthesis: Optional[str]


def im_anchor_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    messages = [
        {"role": "system", "content": IM_ANCHOR_SYSTEM_PROMPT},
        {"role": "user", "content": state["raw_problem"]},
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    new_state["im_summary"] = response.content.strip()
    return new_state  # type: ignore[return-value]


def _with_im_context(state: CouncilState) -> str:
    return (
        "RAW PROBLEM:\n"
        f"{state['raw_problem']}\n\n"
        "IM ANCHOR SUMMARY:\n"
        f"{state.get('im_summary') or ''}"
    )


def sct_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    messages = [
        {"role": "system", "content": SCT_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _with_im_context(state)},
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    outputs = dict(state.get("theory_outputs") or {})
    outputs["sct"] = response.content.strip()
    new_state["theory_outputs"] = outputs
    return new_state  # type: ignore[return-value]


def sdt_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    messages = [
        {"role": "system", "content": SDT_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _with_im_context(state)},
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    outputs = dict(state.get("theory_outputs") or {})
    outputs["sdt"] = response.content.strip()
    new_state["theory_outputs"] = outputs
    return new_state  # type: ignore[return-value]


def wise_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    messages = [
        {"role": "system", "content": WISE_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _with_im_context(state)},
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    outputs = dict(state.get("theory_outputs") or {})
    outputs["wise"] = response.content.strip()
    new_state["theory_outputs"] = outputs
    return new_state  # type: ignore[return-value]


def ra_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    messages = [
        {"role": "system", "content": RA_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _with_im_context(state)},
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    outputs = dict(state.get("theory_outputs") or {})
    outputs["ra"] = response.content.strip()
    new_state["theory_outputs"] = outputs
    return new_state  # type: ignore[return-value]


def env_impl_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    messages = [
        {"role": "system", "content": ENV_IMPL_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _with_im_context(state)},
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    outputs = dict(state.get("theory_outputs") or {})
    outputs["env_impl"] = response.content.strip()
    new_state["theory_outputs"] = outputs
    return new_state  # type: ignore[return-value]


def debate_moderator(state: CouncilState) -> CouncilState:
    llm = get_llm()
    outputs = state.get("theory_outputs") or {}
    combined = [
        f"=== {label} OUTPUT ({key}) ===\n{outputs[key]}"
        for key, label in THEORY_LABELS
        if key in outputs
    ]
    theories_text = "\n\n".join(combined) if combined else "(no theory outputs)"
    messages = [
        {"role": "system", "content": DEBATE_MODERATOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "IM ANCHOR SUMMARY:\n"
                f"{state.get('im_summary') or ''}\n\n"
                "THEORY AGENT OUTPUTS:\n"
                f"{theories_text}"
            ),
        },
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    new_state["debate_summary"] = response.content.strip()
    return new_state  # type: ignore[return-value]


def theory_selector(state: CouncilState) -> CouncilState:
    llm = get_llm()
    outputs = state.get("theory_outputs") or {}
    combined = [
        f"=== {label} OUTPUT ({key}) ===\n{outputs[key]}"
        for key, label in THEORY_LABELS
        if key in outputs
    ]
    theories_text = "\n\n".join(combined) if combined else "(no theory outputs)"
    messages = [
        {"role": "system", "content": THEORY_SELECTOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "IM ANCHOR SUMMARY:\n"
                f"{state.get('im_summary') or ''}\n\n"
                "THEORY AGENT OUTPUTS:\n"
                f"{theories_text}\n\n"
                "DEBATE SUMMARY:\n"
                f"{state.get('debate_summary') or ''}"
            ),
        },
    ]
    response = llm.invoke(messages)
    new_state = dict(state)
    new_state["theory_ranking"] = response.content.strip()
    return new_state  # type: ignore[return-value]


def integrator(state: CouncilState) -> CouncilState:
    llm = get_integrator_llm()
    outputs = state.get("theory_outputs") or {}
    combined = [
        f"=== {label} OUTPUT ({key}) ===\n{outputs[key]}"
        for key, label in THEORY_LABELS
        if key in outputs
    ]
    theories_text = "\n\n".join(combined) if combined else "(no theory outputs)"
    messages = [
        {"role": "system", "content": INTEGRATOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "RAW PROBLEM:\n"
                f"{state['raw_problem']}\n\n"
                "IM ANCHOR SUMMARY:\n"
                f"{state.get('im_summary') or ''}\n\n"
                "THEORY AGENT OUTPUTS:\n"
                f"{theories_text}\n\n"
                "DEBATE SUMMARY:\n"
                f"{state.get('debate_summary') or ''}\n\n"
                "THEORY RANKING AND DECISION NOTE:\n"
                f"{state.get('theory_ranking') or ''}"
            ),
        },
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

    graph.add_node("im_anchor", im_anchor_agent)
    graph.add_node("sct_agent", sct_agent)
    graph.add_node("sdt_agent", sdt_agent)
    graph.add_node("wise_agent", wise_agent)
    graph.add_node("ra_agent", ra_agent)
    graph.add_node("env_impl_agent", env_impl_agent)
    graph.add_node("debate_moderator", debate_moderator)
    graph.add_node("theory_selector", theory_selector)
    graph.add_node("integrator", integrator)

    graph.set_entry_point("im_anchor")
    graph.add_edge("im_anchor", "sct_agent")
    graph.add_edge("sct_agent", "sdt_agent")
    graph.add_edge("sdt_agent", "wise_agent")
    graph.add_edge("wise_agent", "ra_agent")
    graph.add_edge("ra_agent", "env_impl_agent")
    graph.add_edge("env_impl_agent", "debate_moderator")
    graph.add_edge("debate_moderator", "theory_selector")
    graph.add_edge("theory_selector", "integrator")
    graph.add_edge("integrator", END)

    return graph.compile()


def get_app() -> Any:
    """
    Convenience helper for callers that just need the compiled graph.
    """
    return build_graph()


__all__ = [
    "CouncilState",
    "im_anchor_agent",
    "sct_agent",
    "sdt_agent",
    "wise_agent",
    "ra_agent",
    "env_impl_agent",
    "debate_moderator",
    "theory_selector",
    "integrator",
    "build_graph",
    "get_app",
]


