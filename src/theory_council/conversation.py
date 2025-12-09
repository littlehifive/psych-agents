"""
Conversation routing utilities for switching between standard GPT chat and the
multi-agent Theory Council workflow.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict

from .chat import ChatMessage, generate_chat_response
from .graph import CouncilPipelineResult, run_council_pipeline
from .orchestration import InMemorySessionStore

ConversationMode = Literal["chat", "agent"]


class ConversationOutcome(TypedDict, total=False):
    """
    Unified payload returned after processing a user turn.
    """

    mode: ConversationMode
    session_id: str
    messages: List[ChatMessage]
    assistant_message: ChatMessage
    agent_result: CouncilPipelineResult
    auto_disable_agent: bool


def _latest_user_utterance(messages: List[ChatMessage]) -> Optional[str]:
    for message in reversed(messages):
        if message["role"] == "user":
            return message["content"]
    return None


def process_conversation_turn(
    *,
    session_store: InMemorySessionStore,
    session_id: str,
    messages: List[ChatMessage],
    agent_enabled: bool,
    metadata: Optional[Dict[str, Any]] = None,
) -> ConversationOutcome:
    """
    Route the incoming turn through either the lightweight GPT chat helper or
    the full multi-agent Theory Council workflow.
    """

    session_store.replace_messages(session_id, messages)

    if not agent_enabled:
        chat_result = generate_chat_response(messages, metadata=metadata)
        assistant_message = chat_result["messages"][-1]
        session_store.replace_messages(session_id, chat_result["messages"])
        return {
            "mode": "chat",
            "session_id": session_id,
            "messages": chat_result["messages"],
            "assistant_message": assistant_message,
            "auto_disable_agent": False,
        }

    problem_statement = _latest_user_utterance(messages)
    if not problem_statement:
        raise ValueError("Agent mode requires a user problem statement.")

    agent_result = run_council_pipeline(problem_statement, metadata=metadata)
    assistant_message: ChatMessage = {
        "role": "assistant",
        "content": agent_result["final_synthesis"],
    }
    session_store.append_message(session_id, assistant_message)

    return {
        "mode": "agent",
        "session_id": session_id,
        "messages": session_store.get_or_create(session_id)["messages"],
        "assistant_message": assistant_message,
        "agent_result": agent_result,
        "auto_disable_agent": True,
    }


__all__ = ["process_conversation_turn", "ConversationMode", "ConversationOutcome"]

