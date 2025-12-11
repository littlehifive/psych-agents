"""
Lightweight GPT chat helper for conversational follow-ups that do not require
the full Theory Council pipeline.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict

from .config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, get_llm

ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: ChatRole
    content: str


class ChatResult(TypedDict, total=False):
    response: str
    messages: List[ChatMessage]
    model: str


DEFAULT_CHAT_MODEL = DEFAULT_MODEL
DEFAULT_CHAT_TEMPERATURE = min(0.5, DEFAULT_TEMPERATURE)


GENERAL_CHAT_SYSTEM_PROMPT = """
You are an expert psychological theory assistant helping researchers design social interventions.
Your goal is to help them apply theories (like SCT, SDT, TPB, etc.) practically to the interventions they are designing in the social sector.
Always aim to be practical, using theoretical frameworks to identify specific determinants (e.g., self-efficacy, norms) and matching methods.
"""


def generate_chat_response(
    messages: List[ChatMessage],
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ChatResult:
    """
    Return a short GPT-only response so the UI can continue a conversation
    without spinning up the multi-agent workflow.
    """
    # Ensure our specialized system prompt is present if the conversation doesn't have one
    current_messages = list(messages)
    if not current_messages or current_messages[0]["role"] != "system":
        current_messages.insert(0, {"role": "system", "content": GENERAL_CHAT_SYSTEM_PROMPT})

    llm = get_llm(
        model=model or DEFAULT_CHAT_MODEL,
        temperature=temperature if temperature is not None else DEFAULT_CHAT_TEMPERATURE,
    )

    invoke_kwargs: Dict[str, Any] = {}
    if metadata:
        invoke_kwargs["config"] = {"metadata": metadata}

    response = llm.invoke(current_messages, **invoke_kwargs)
    content = response.content.strip()
    model_name = getattr(llm, "model_name", model or DEFAULT_CHAT_MODEL)

    return {
        "response": content,
        "messages": [*messages, {"role": "assistant", "content": content}],
        "model": model_name,
    }


__all__ = ["ChatMessage", "ChatResult", "generate_chat_response", "GENERAL_CHAT_SYSTEM_PROMPT"]

