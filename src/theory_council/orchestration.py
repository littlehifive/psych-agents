"""
Orchestration utilities that decide when to escalate to the Theory Council and
keep lightweight session state for the chat endpoint.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from .chat import ChatMessage
from .graph import CouncilPipelineResult

ESCALATION_KEYWORDS = {
    "analysis",
    "analyze",
    "council",
    "debate",
    "full plan",
    "im guide",
    "intervention design",
    "mapping",
    "multi-agent",
    "run council",
    "strategy",
    "theory",
}


class SessionState(TypedDict, total=False):
    session_id: str
    messages: List[ChatMessage]
    last_run_id: Optional[str]
    last_council_result: Optional[CouncilPipelineResult]


class InMemorySessionStore:
    """
    Simplistic in-memory store for chat sessions. Swap out later for Redis/DB.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}

    def get(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str) -> SessionState:
        session = self._sessions.get(session_id)
        if session:
            return session
        session = {
            "session_id": session_id,
            "messages": [],
            "last_run_id": None,
            "last_council_result": None,
        }
        self._sessions[session_id] = session
        return session

    def replace_messages(self, session_id: str, messages: List[ChatMessage]) -> SessionState:
        session = self.get_or_create(session_id)
        session["messages"] = list(messages)
        return session

    def append_message(self, session_id: str, message: ChatMessage) -> SessionState:
        session = self.get_or_create(session_id)
        session.setdefault("messages", []).append(message)
        return session

    def record_council_run(self, session_id: str, run_id: str, result: CouncilPipelineResult) -> SessionState:
        session = self.get_or_create(session_id)
        session["last_run_id"] = run_id
        session["last_council_result"] = result
        return session


def _extract_last_user_message(messages: List[ChatMessage]) -> Optional[str]:
    for message in reversed(messages):
        if message["role"] == "user":
            return message["content"]
    return None


def should_escalate_to_council(
    messages: List[ChatMessage],
    *,
    session_state: Optional[SessionState] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Decide whether to spin up the full Theory Council based on the latest message.
    """
    if metadata and metadata.get("escalate") is True:
        return True

    last_user_message = _extract_last_user_message(messages)
    if not last_user_message:
        return False

    text = last_user_message.strip().lower()
    if metadata and metadata.get("force_council"):
        return True

    if any(keyword in text for keyword in ESCALATION_KEYWORDS):
        return True

    word_count = len(text.split())
    if word_count >= 120 or len(text) > 800:
        return True

    has_prior_run = bool(session_state and session_state.get("last_run_id"))
    if not has_prior_run and word_count >= 40:
        return True

    return False


__all__ = [
    "InMemorySessionStore",
    "SessionState",
    "should_escalate_to_council",
]

