"""
FastAPI server that exposes the Theory Council pipeline and a lightweight chat endpoint.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Literal, Optional, TypedDict
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from theory_council.chat import ChatMessage as ChatMessageDict
from theory_council.config import get_langsmith_settings
from theory_council.conversation import ConversationOutcome, process_conversation_turn
from theory_council.graph import (
    CouncilPipelineResult,
    CouncilState,
    run_council_pipeline,
    stream_council_pipeline,
)
from theory_council.orchestration import InMemorySessionStore

logger = logging.getLogger("theory_council.server")
logging.basicConfig(level=logging.INFO)

langsmith_settings = get_langsmith_settings()
for key, value in langsmith_settings.items():
    if value and not os.environ.get(key):
        os.environ[key] = value
        logger.debug("Configured %s for LangSmith observability.", key)

if langsmith_settings.get("LANGCHAIN_API_KEY") and not os.environ.get("LANGCHAIN_TRACING_V2"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

app = FastAPI(
    title="Theory Council API",
    description="Expose the LangGraph-based Theory Council workflow and supporting chat helpers.",
    version="0.1.0",
)

_default_origins = "http://localhost:3000,http://127.0.0.1:3000"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("COUNCIL_ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRecord(TypedDict):
    result: CouncilPipelineResult
    session_id: Optional[str]


RUN_LOG: Dict[str, RunRecord] = {}
SESSION_STORE = InMemorySessionStore()


class AgentTraceModel(BaseModel):
    agent_key: str
    agent_label: str
    output: str
    started_at: str
    completed_at: str
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class CouncilResultModel(BaseModel):
    raw_problem: str
    framed_problem: Optional[str] = None
    im_summary: Optional[str] = None
    theory_outputs: Dict[str, str]
    debate_summary: Optional[str] = None
    theory_ranking: Optional[str] = None
    final_synthesis: str = ""
    sections: Dict[str, str]
    agent_traces: List[AgentTraceModel]


class CouncilRunRequest(BaseModel):
    problem: str = Field(..., description="Raw behavior-change or implementation challenge description.")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata to forward into the LangGraph config (e.g., user id).",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session to associate this run with.",
    )
    chat_history: Optional[List[ChatMessageModel]] = Field(
        default=None,
        description="Optional conversation history to provide context for the agent.",
    )


class CouncilRunResponse(BaseModel):
    run_id: str
    status: Literal["completed"]
    result: CouncilResultModel
    session_id: Optional[str] = None


class ChatMessageModel(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

    def to_dict(self) -> ChatMessageDict:
        return {"role": self.role, "content": self.content}


class ConversationRequest(BaseModel):
    messages: List[ChatMessageModel]
    agent_enabled: bool = Field(
        default=False,
        description="When true, trigger the full multi-agent Theory Council workflow for this turn.",
    )
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = Field(
        default=None,
        description="Conversation/session identifier for continuous learning.",
    )


class ConversationResponseModel(BaseModel):
    session_id: str
    mode: Literal["chat", "agent"]
    assistant_message: ChatMessageModel
    messages: List[ChatMessageModel]
    agent_result: Optional[CouncilResultModel] = None
    run_id: Optional[str] = None
    auto_disable_agent: bool = False


def _store_run(result: CouncilPipelineResult, session_id: Optional[str] = None) -> str:
    run_id = uuid4().hex
    RUN_LOG[run_id] = {"result": result, "session_id": session_id}
    return run_id


def _build_council_result_model(result: CouncilPipelineResult) -> CouncilResultModel:
    return CouncilResultModel(**result)


def _make_council_run_response(
    run_id: str, run_result: CouncilPipelineResult, session_id: Optional[str]
) -> CouncilRunResponse:
    return CouncilRunResponse(
        run_id=run_id,
        status="completed",
        result=_build_council_result_model(run_result),
        session_id=session_id,
    )


def _format_sse(event: str, payload: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/council/run", response_model=CouncilRunResponse)
def council_run_endpoint(payload: CouncilRunRequest) -> CouncilRunResponse:
    session_id = payload.session_id or uuid4().hex
    run_result = run_council_pipeline(payload.problem, metadata=payload.metadata)
    run_id = _store_run(run_result, session_id=session_id)
    SESSION_STORE.record_council_run(session_id, run_id, run_result)
    return _make_council_run_response(run_id, run_result, session_id)


@app.get("/council/run/{run_id}", response_model=CouncilRunResponse)
def get_council_run(run_id: str) -> CouncilRunResponse:
    record = RUN_LOG.get(run_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Run id '{run_id}' not found.")
    return _make_council_run_response(run_id, record["result"], record.get("session_id"))


@app.post("/council/run/stream")
async def stream_council_run(payload: CouncilRunRequest) -> StreamingResponse:
    session_id = payload.session_id or uuid4().hex

    def event_stream():
        yield _format_sse("started", {"session_id": session_id})

        # We need to collect the final result to store it, so we track state
        final_state: Optional[CouncilState] = None

        # Iterate over the blocking generator
        # Note: In production with many users, we'd want to offload this to a task queue
        # or use run_in_executor to avoid blocking the thread if not using async graph.
        # Here we rely on FastAPI threading the sync generator response.
        history_dicts = [m.to_dict() for m in (payload.chat_history or [])]
        for state in stream_council_pipeline(
            payload.problem,
            metadata=payload.metadata,
            chat_history=history_dicts,
        ):
            final_state = state
            # Emit the NEWEST trace if present
            traces = state.get("agent_traces") or []
            if traces:
                latest_trace = traces[-1]
                # We can construct a run_id immediately or wait?
                # The prompt implies we need a run_id for the trace event.
                # Let's generate one upfront.
                temp_run_id = "pending-run"
                yield _format_sse("trace", {"trace": latest_trace, "run_id": temp_run_id})

        if final_state:
            # Reconstruct the full pipeline result
            final_text = (final_state.get("final_synthesis") or "").strip()
            # We need to import _parse_integrator_sections or duplicate logic.
            # Ideally run_council_pipeline logic should be reused.
            # For now, let's just minimal reconstruction or assume client handles partials?
            # Client expects "complete" event with "CouncilRunResponse".
            # We must save the run to DB/Memory.
            from theory_council.graph import _parse_integrator_sections  # lazy import or move helper

            sections = _parse_integrator_sections(final_text)
            full_result: CouncilPipelineResult = {
                "raw_problem": payload.problem,
                "framed_problem": final_state.get("framed_problem"),
                "im_summary": final_state.get("im_summary"),
                "theory_outputs": final_state.get("theory_outputs") or {},
                "debate_summary": final_state.get("debate_summary"),
                "theory_ranking": final_state.get("theory_ranking"),
                "final_synthesis": final_text,
                "sections": sections,
                "agent_traces": final_state.get("agent_traces") or [],
            }
            
            run_id = _store_run(full_result, session_id=session_id)
            SESSION_STORE.record_council_run(session_id, run_id, full_result)
            
            response_payload = _make_council_run_response(run_id, full_result, session_id)
            yield _format_sse("complete", {"run": response_payload.model_dump()})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/conversation/send", response_model=ConversationResponseModel)
def conversation_endpoint(payload: ConversationRequest) -> ConversationResponseModel:
    if not payload.messages:
        raise HTTPException(status_code=400, detail="At least one message is required.")

    session_id = payload.session_id or uuid4().hex
    chat_messages = [msg.to_dict() for msg in payload.messages]

    outcome = process_conversation_turn(
        session_store=SESSION_STORE,
        session_id=session_id,
        messages=chat_messages,
        agent_enabled=payload.agent_enabled,
        metadata=payload.metadata,
    )

    agent_result_model: Optional[CouncilResultModel] = None
    run_id: Optional[str] = None

    if outcome.get("agent_result"):
        run_result = outcome["agent_result"]  # type: ignore[index]
        run_id = _store_run(run_result, session_id=session_id)
        SESSION_STORE.record_council_run(session_id, run_id, run_result)
        agent_result_model = _build_council_result_model(run_result)

    response_messages = [ChatMessageModel(**message) for message in outcome["messages"]]
    assistant_message = ChatMessageModel(**outcome["assistant_message"])

    return ConversationResponseModel(
        session_id=outcome["session_id"],
        mode=outcome["mode"],
        assistant_message=assistant_message,
        messages=response_messages,
        agent_result=agent_result_model,
        run_id=run_id,
        auto_disable_agent=outcome.get("auto_disable_agent", False),
    )


__all__ = ["app"]

