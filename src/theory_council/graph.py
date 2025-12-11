"""
LangGraph state and node definitions for the Theory Council workflow.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict, Iterator

from langgraph.graph import END, StateGraph

from .config import get_integrator_llm, get_llm
from .personas import (
    DEBATE_MODERATOR_SYSTEM_PROMPT,
    ENV_IMPL_AGENT_SYSTEM_PROMPT,
    IM_ANCHOR_SYSTEM_PROMPT,
    INTEGRATOR_SYSTEM_PROMPT,
    PROBLEM_FRAMER_SYSTEM_PROMPT,
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


class AgentTrace(TypedDict, total=False):
    """
    Lightweight representation of an agent run for timeline displays.
    """

    agent_key: str
    agent_label: str
    output: str
    started_at: str
    completed_at: str
    duration_ms: float
    metadata: Dict[str, Any]


class CouncilState(TypedDict):
    """
    The shared state passed between Theory Council agents.
    """

    raw_problem: str
    framed_problem: Optional[str]
    im_summary: Optional[str]
    theory_outputs: Dict[str, str]
    debate_summary: Optional[str]
    theory_ranking: Optional[str]
    final_synthesis: Optional[str]
    agent_traces: List[AgentTrace]


class CouncilPipelineResult(TypedDict):
    """
    Structured output returned by run_council_pipeline.
    """

    raw_problem: str
    framed_problem: Optional[str]
    im_summary: Optional[str]
    theory_outputs: Dict[str, str]
    debate_summary: Optional[str]
    theory_ranking: Optional[str]
    final_synthesis: str
    sections: Dict[str, str]
    agent_traces: List[AgentTrace]


SECTION_HEADERS = [
    ("1. Problem Framing", "problem_framing"),
    ("2. Theory Council Debate", "theory_council_debate"),
    ("3. Intervention Mapping Guide", "intervention_mapping_guide"),
    ("4. Recommended Intervention Concept(s)", "recommended_intervention_concepts"),
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _record_agent_progress(
    state: CouncilState,
    *,
    agent_key: str,
    agent_label: str,
    content: str,
    started_at: datetime,
    completed_at: datetime,
    metadata: Optional[Dict[str, Any]] = None,
    updates: Optional[Dict[str, Any]] = None,
) -> CouncilState:
    trace: AgentTrace = {
        "agent_key": agent_key,
        "agent_label": agent_label,
        "output": content,
        "started_at": started_at.isoformat(),
        "completed_at": completed_at.isoformat(),
        "duration_ms": max((completed_at - started_at).total_seconds() * 1000, 0.0),
    }
    if metadata:
        trace["metadata"] = metadata
    traces = list(state.get("agent_traces") or [])
    traces.append(trace)
    new_state = dict(state)
    if updates:
        new_state.update(updates)
    new_state["agent_traces"] = traces
    return new_state  # type: ignore[return-value]


def _theory_label(slug: str) -> str:
    for key, label in THEORY_LABELS:
        if key == slug:
            return label
    return slug


def _problem_context(state: CouncilState) -> str:
    framed = state.get("framed_problem") or ""
    return (
        "RAW PROBLEM:\n"
        f"{state['raw_problem']}\n\n"
        "AI-FRAMED PROBLEM:\n"
        f"{framed}".strip()
    )


def _theory_agent_context(state: CouncilState) -> str:
    return (
        _problem_context(state)
        + "\n\nIM ANCHOR SUMMARY:\n"
        + (state.get("im_summary") or "")
    )


def _combined_theory_outputs(state: CouncilState) -> str:
    outputs = state.get("theory_outputs") or {}
    combined = [
        f"=== {_theory_label(key)} OUTPUT ({key}) ===\n{outputs[key]}"
        for key, _ in THEORY_LABELS
        if key in outputs
    ]
    return "\n\n".join(combined) if combined else "(no theory outputs yet)"


def problem_framer(state: CouncilState) -> CouncilState:
    llm = get_llm()
    started = _now()
    messages = [
        {"role": "system", "content": PROBLEM_FRAMER_SYSTEM_PROMPT},
        {"role": "user", "content": state["raw_problem"]},
    ]
    response = llm.invoke(messages)
    completed = _now()
    content = response.content.strip()
    return _record_agent_progress(
        state,
        agent_key="problem_framer",
        agent_label="Problem Framer",
        content=content,
        started_at=started,
        completed_at=completed,
        metadata={"category": "framing"},
        updates={"framed_problem": content},
    )


def im_anchor_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    started = _now()
    messages = [
        {"role": "system", "content": IM_ANCHOR_SYSTEM_PROMPT},
        {"role": "user", "content": _problem_context(state)},
    ]
    response = llm.invoke(messages)
    completed = _now()
    content = response.content.strip()
    return _record_agent_progress(
        state,
        agent_key="im_anchor",
        agent_label="IM Anchor",
        content=content,
        started_at=started,
        completed_at=completed,
        metadata={"category": "anchor"},
        updates={"im_summary": content},
    )


def sct_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    started = _now()
    messages = [
        {"role": "system", "content": SCT_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _theory_agent_context(state)},
    ]
    response = llm.invoke(messages)
    outputs = dict(state.get("theory_outputs") or {})
    content = response.content.strip()
    outputs["sct"] = content
    completed = _now()
    return _record_agent_progress(
        state,
        agent_key="sct",
        agent_label=_theory_label("sct"),
        content=content,
        started_at=started,
        completed_at=completed,
        metadata={"category": "theory", "theory_key": "sct"},
        updates={"theory_outputs": outputs},
    )


def sdt_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    started = _now()
    messages = [
        {"role": "system", "content": SDT_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _theory_agent_context(state)},
    ]
    response = llm.invoke(messages)
    outputs = dict(state.get("theory_outputs") or {})
    content = response.content.strip()
    outputs["sdt"] = content
    completed = _now()
    return _record_agent_progress(
        state,
        agent_key="sdt",
        agent_label=_theory_label("sdt"),
        content=content,
        started_at=started,
        completed_at=completed,
        metadata={"category": "theory", "theory_key": "sdt"},
        updates={"theory_outputs": outputs},
    )


def wise_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    started = _now()
    messages = [
        {"role": "system", "content": WISE_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _theory_agent_context(state)},
    ]
    response = llm.invoke(messages)
    outputs = dict(state.get("theory_outputs") or {})
    content = response.content.strip()
    outputs["wise"] = content
    completed = _now()
    return _record_agent_progress(
        state,
        agent_key="wise",
        agent_label=_theory_label("wise"),
        content=content,
        started_at=started,
        completed_at=completed,
        metadata={"category": "theory", "theory_key": "wise"},
        updates={"theory_outputs": outputs},
    )


def ra_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    started = _now()
    messages = [
        {"role": "system", "content": RA_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _theory_agent_context(state)},
    ]
    response = llm.invoke(messages)
    outputs = dict(state.get("theory_outputs") or {})
    content = response.content.strip()
    outputs["ra"] = content
    completed = _now()
    return _record_agent_progress(
        state,
        agent_key="ra",
        agent_label=_theory_label("ra"),
        content=content,
        started_at=started,
        completed_at=completed,
        metadata={"category": "theory", "theory_key": "ra"},
        updates={"theory_outputs": outputs},
    )


def env_impl_agent(state: CouncilState) -> CouncilState:
    llm = get_llm()
    started = _now()
    messages = [
        {"role": "system", "content": ENV_IMPL_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": _theory_agent_context(state)},
    ]
    response = llm.invoke(messages)
    outputs = dict(state.get("theory_outputs") or {})
    content = response.content.strip()
    outputs["env_impl"] = content
    completed = _now()
    return _record_agent_progress(
        state,
        agent_key="env_impl",
        agent_label=_theory_label("env_impl"),
        content=content,
        started_at=started,
        completed_at=completed,
        metadata={"category": "theory", "theory_key": "env_impl"},
        updates={"theory_outputs": outputs},
    )


def debate_moderator(state: CouncilState) -> CouncilState:
    llm = get_llm()
    started = _now()
    theories_text = _combined_theory_outputs(state)
    messages = [
        {"role": "system", "content": DEBATE_MODERATOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                _problem_context(state)
                + "\n\nIM ANCHOR SUMMARY:\n"
                f"{state.get('im_summary') or ''}\n\n"
                "THEORY AGENT OUTPUTS:\n"
                f"{theories_text}"
            ),
        },
    ]
    response = llm.invoke(messages)
    completed = _now()
    content = response.content.strip()
    return _record_agent_progress(
        state,
        agent_key="debate_moderator",
        agent_label="Debate Moderator",
        content=content,
        started_at=started,
        completed_at=completed,
        metadata={"category": "synthesis"},
        updates={"debate_summary": content},
    )


def theory_selector(state: CouncilState) -> CouncilState:
    llm = get_llm()
    started = _now()
    theories_text = _combined_theory_outputs(state)
    messages = [
        {"role": "system", "content": THEORY_SELECTOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                _problem_context(state)
                + "\n\nIM ANCHOR SUMMARY:\n"
                f"{state.get('im_summary') or ''}\n\n"
                "THEORY AGENT OUTPUTS:\n"
                f"{theories_text}\n\n"
                "DEBATE SUMMARY:\n"
                f"{state.get('debate_summary') or ''}"
            ),
        },
    ]
    response = llm.invoke(messages)
    completed = _now()
    content = response.content.strip()
    return _record_agent_progress(
        state,
        agent_key="theory_selector",
        agent_label="Theory Selector",
        content=content,
        started_at=started,
        completed_at=completed,
        metadata={"category": "decision"},
        updates={"theory_ranking": content},
    )


def integrator(state: CouncilState) -> CouncilState:
    llm = get_integrator_llm()
    started = _now()
    theories_text = _combined_theory_outputs(state)
    messages = [
        {"role": "system", "content": INTEGRATOR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                _problem_context(state)
                + "\n\nIM ANCHOR SUMMARY:\n"
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
    completed = _now()
    content = response.content.strip()
    return _record_agent_progress(
        state,
        agent_key="integrator",
        agent_label="Integrator",
        content=content,
        started_at=started,
        completed_at=completed,
        metadata={"category": "integrator"},
        updates={"final_synthesis": content},
    )


def build_graph() -> Any:
    """
    Assemble and compile the sequential Theory Council graph.
    """
    graph = StateGraph(CouncilState)

    graph.add_node("problem_framer", problem_framer)
    graph.add_node("im_anchor", im_anchor_agent)
    graph.add_node("sct_agent", sct_agent)
    graph.add_node("sdt_agent", sdt_agent)
    graph.add_node("wise_agent", wise_agent)
    graph.add_node("ra_agent", ra_agent)
    graph.add_node("env_impl_agent", env_impl_agent)
    graph.add_node("debate_moderator", debate_moderator)
    graph.add_node("theory_selector", theory_selector)
    graph.add_node("integrator", integrator)

    graph.set_entry_point("problem_framer")
    graph.add_edge("problem_framer", "im_anchor")
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


def _parse_integrator_sections(text: str) -> Dict[str, str]:
    """
    Split the integrator output into the four expected sections for the UI.
    """
    sections = {key: "" for _, key in SECTION_HEADERS}
    if not text.strip():
        return sections

    header_lookup = {header: key for header, key in SECTION_HEADERS}
    current_key: Optional[str] = None
    buffer: List[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        matched_key = next(
            (header_lookup[header] for header in header_lookup if stripped.startswith(header)),
            None,
        )
        if matched_key:
            if current_key is not None:
                sections[current_key] = "\n".join(buffer).strip()
            current_key = matched_key
            buffer = []
        else:
            if current_key is not None:
                buffer.append(line)

    if current_key is not None:
        sections[current_key] = "\n".join(buffer).strip()

    return sections


def run_council_pipeline(
    problem: str,
    *,
    metadata: Optional[Dict[str, Any]] = None,
    app: Optional[Any] = None,
) -> CouncilPipelineResult:
    """
    High-level helper to execute the LangGraph workflow and return structured output.
    """
    initial_state: CouncilState = {
        "raw_problem": problem,
        "framed_problem": None,
        "im_summary": None,
        "theory_outputs": {},
        "debate_summary": None,
        "theory_ranking": None,
        "final_synthesis": None,
        "agent_traces": [],
    }

    compiled = app or get_app()
    invoke_kwargs: Dict[str, Any] = {}
    if metadata:
        invoke_kwargs["config"] = {"metadata": metadata}

    result: CouncilState = compiled.invoke(initial_state, **invoke_kwargs)
    final_text = (result.get("final_synthesis") or "").strip()
    sections = _parse_integrator_sections(final_text)

    return {
        "raw_problem": problem,
        "framed_problem": result.get("framed_problem"),
        "im_summary": result.get("im_summary"),
        "theory_outputs": result.get("theory_outputs") or {},
        "debate_summary": result.get("debate_summary"),
        "theory_ranking": result.get("theory_ranking"),
        "final_synthesis": final_text,
        "sections": sections,
        "agent_traces": result.get("agent_traces") or [],
    }


def stream_council_pipeline(
    problem: str,
    *,
    metadata: Optional[Dict[str, Any]] = None,
    app: Optional[Any] = None,
) -> Iterator[CouncilState]:
    """
    Generator that yields updates from the Council pipeline as agents complete.
    """
    initial_state: CouncilState = {
        "raw_problem": problem,
        "framed_problem": None,
        "im_summary": None,
        "theory_outputs": {},
        "debate_summary": None,
        "theory_ranking": None,
        "final_synthesis": None,
        "agent_traces": [],
    }

    compiled = app or get_app()
    invoke_kwargs: Dict[str, Any] = {}
    if metadata:
        invoke_kwargs["config"] = {"metadata": metadata}

    for step_output in compiled.stream(initial_state, **invoke_kwargs):
        # step_output is like {"node_name": updated_state}
        for _, state in step_output.items():
            yield state


__all__ = [
    "AgentTrace",
    "CouncilState",
    "CouncilPipelineResult",
    "problem_framer",
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
    "run_council_pipeline",
    "stream_council_pipeline",
]


