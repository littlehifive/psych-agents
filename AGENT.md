# Theory Council Agent Architecture

## Overview
The **Theory Council** is a multi-agent system designed to help users apply psychological theories to social intervention design. It uses **LangGraph** to orchestrate a sequence of specialized agents that analyze a problem, apply specific theoretical lenses, debate the findings, and synthesize a practical intervention plan.

## Core Architecture
The system is built on:
- **LangChain/LangGraph**: For agent orchestration and state management.
- **FastAPI**: Serving the agent pipeline via REST and Server-Sent Events (SSE).
- **Next.js**: Frontend for user interaction and visualization.

## Agent Pipeline (Sequential)
The web of agents currently operates in a sequential pipeline defined in `src/theory_council/graph.py`:

1.  **Problem Framer** (`problem_framer`)
    - Takes the raw user input.
    - REFRAMES it into a structured, actionable problem statement.
    - *Output*: `framed_problem`

2.  **Intervention Mapping (IM) Anchor** (`im_anchor`)
    - Analyzes the framed problem using Intervention Mapping principles.
    - Identifies target populations, behaviors, and environmental conditions.
    - *Output*: `im_summary`

3.  **Theory Agents** (Run sequentially)
    Each agent applies a specific psychological framework to the problem and IM anchor.
    - **SCT Agent** (`sct_agent`): Social Cognitive Theory.
    - **SDT Agent** (`sct_agent`): Self-Determination Theory.
    - **Wise Agent** (`wise_agent`): Wise Interventions / Belonging.
    - **Reasoned Action Agent** (`ra_agent`): TPB / Reasoned Action.
    - **Environment & Implementation Agent** (`env_impl_agent`): implementation science.
    - *Output*: Accumulated `theory_outputs` dictionary.

4.  **Debate Moderator** (`debate_moderator`)
    - Reviews all theory outputs.
    - Synthesizes complementarities, tensions, and unique insights.
    - *Output*: `debate_summary`

5.  **Theory Selector** (`theory_selector`)
    - Ranks theories based on relevance to the specific problem.
    - Provides a decision note on which lenses to prioritize.
    - *Output*: `theory_ranking`

6.  **Integrator** (`integrator`)
    - Takes all previous outputs (framing, IM anchor, theories, debate, selection).
    - Produces a final **4-section report**:
        1. Problem Framing
        2. Theory Council Debate
        3. Intervention Mapping Guide
        4. Recommended Intervention Concept(s)
    - *Output*: `final_synthesis`

## Data Flow & State
The `CouncilState` (TypedDict) maintains the context across steps:
```python
class CouncilState(TypedDict):
    raw_problem: str
    framed_problem: Optional[str]
    im_summary: Optional[str]
    theory_outputs: Dict[str, str]
    debate_summary: Optional[str]
    theory_ranking: Optional[str]
    final_synthesis: Optional[str]
    agent_traces: List[AgentTrace]
```

## Visualization
- The backend streams execution progress via SSE (`/council/run/stream`).
- Events include `started`, `trace` (for each agent step completion), and `complete`.
- The frontend `AgentFlowVisualizer` consumes these traces to display the process.
