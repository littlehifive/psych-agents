"""
Lightweight GPT chat helper for conversational follow-ups that do not require
the full Theory Council pipeline.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict

from .config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, get_llm
from .rag import query_context, format_context_for_prompt

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

GUIDANCE ON CLARIFICATION & AGENT MODE RECOMMENDATION:
1. If the user presents a vague or new problem (e.g., "I want to improve school lunches"), DO NOT immediately solve it. Instead, ask 3-4 structured clarifying questions to help frame the problem.
   - Ask about the Target Audience (Who exactly?).
   - Ask about the specific Desired Behaviors (What do they need to do?).
   - Ask about potential Barriers/Context (Why aren't they doing it?).
2. If the user provides a detailed problem or answers your questions, ACKNOWLEDGE the context, and explicitly RECOMMEND they toggle the "Agent" mode for a full deep-dive analysis.
   - Example: "This is excellent context. To systematically apply theory to this problem, I recommend you toggle the 'Agent' switch below and hit Send to run a full analysis."
3. Always be practical, warm, and professional.
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

    # RAG Integration
    last_user_msg = next((m for m in reversed(current_messages) if m["role"] == "user"), None)
    if last_user_msg:
        try:
            chunks = query_context(last_user_msg["content"])
            if chunks:
                context_str = format_context_for_prompt(chunks)
                # Insert context as a system message right before the history or appended to system prompt
                # To ensure it is seen as "fresh" info, we can append it to the system prompt or add a new system message
                # Let's add it as a new system message after the main one
                current_messages.insert(1, {
                    "role": "system",
                    "content": f"{context_str}\n\nINSTRUCTION: Use the above context to answer the user's question if relevant. "
                               "Cite the source PDFs and page numbers explicitly (e.g., [Bandura, 1977, p.5]) when using this information."
                })
        except Exception as e:
            # Fallback if RAG fails, don't break the chat
            print(f"RAG retrieval failed: {e}")

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

