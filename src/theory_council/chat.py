"""
Lightweight Chat Helper using Google Gemini File Search (Server-Side RAG).
Replaces previous OpenAI-based basic chat to leverage Gemini's long context and native retrieval.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Literal, Optional, TypedDict

from google import genai
from google.genai import types

from .config import get_google_api_key
from .gemini_store import get_or_create_store
try:
    from langsmith import traceable
except ImportError:
    # Fallback no-op decorator if langsmith is missing
    def traceable(op_name=None):
        def decorator(func):
            return func
        return decorator

logger = logging.getLogger("theory_council.chat")

ChatRole = Literal["system", "user", "assistant"]

class ChatMessage(TypedDict):
    role: ChatRole
    content: str
    
class ChatResult(TypedDict, total=False):
    response: str
    messages: List[ChatMessage]
    model: str
    
DEFAULT_CHAT_MODEL = "gemini-2.5-flash"

GENERAL_CHAT_SYSTEM_PROMPT = """
You are an expert psychological theory assistant helping researchers design social interventions.
Your goal is to help them apply theories (like SCT, SDT, TPB, etc.) practically.

CONTEXT INSTRUCTIONS:
You have access to a 'FileSearch' tool containing the user's uploaded context documents (PDFs).
- ALWAYS search the files when the user asks a question about specific theories, definitions, or the content of the uploaded documents.
- If the files contain the answer, cite the source using the tool's citation format.
- If the files do not contain the answer, rely on your general knowledge but mention that it's not in the context.

GUIDANCE ON CLARIFICATION & AGENT MODE RECOMMENDATION:
1. If the user presents a vague or new problem (e.g., "I want to improve school lunches"), DO NOT immediately solve it. Instead, ask 3-4 structured clarifying questions to help frame the problem.
   - Ask about the Target Audience (Who exactly?).
   - Ask about the specific Desired Behaviors (What do they need to do?).
   - Ask about potential Barriers/Context (Why aren't they doing it?).
2. If the user provides a detailed problem or answers your questions, ACKNOWLEDGE the context, and explicitly RECOMMEND they toggle the "Agent" mode for a full deep-dive analysis.
   - Example: "This is excellent context. To systematically apply theory to this problem, I recommend you toggle the 'Agent' switch below and hit Send to run a full analysis."
3. Always be practical, warm, and professional.
"""

def _build_gemini_client() -> genai.Client:
    return genai.Client(api_key=get_google_api_key())

def _prepare_gemini_config(target_model: str) -> types.GenerateContentConfig:
    try:
        client = _build_gemini_client()
        # Find the store we synced to
        store = get_or_create_store(client)
        
        file_search_tool = types.Tool(
            file_search=types.FileSearch(
                file_search_store_names=[store.name]
            )
        )
        return types.GenerateContentConfig(
            tools=[file_search_tool],
            system_instruction=GENERAL_CHAT_SYSTEM_PROMPT,
            temperature=0.3
        )
    except Exception as e:
        logger.error("Failed to prepare Gemini File Search config: %s", e)
        return types.GenerateContentConfig(
            system_instruction=GENERAL_CHAT_SYSTEM_PROMPT,
            temperature=0.3
        )

@traceable(run_type="llm", name="Gemini Chat (Sync)")
def generate_chat_response(
    messages: List[ChatMessage],
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ChatResult:
    """
    Generate a response using Google Gemini (Sync).
    """
    client = _build_gemini_client()
    target_model = model or DEFAULT_CHAT_MODEL
    
    # Format messages for Gemini
    gemini_contents = []
    for msg in messages:
        if msg["role"] == "system":
            continue
        role = "user" if msg["role"] == "user" else "model"
        gemini_contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
        
    if not gemini_contents:
        gemini_contents.append(types.Content(role="user", parts=[types.Part(text="Hello")]))

    try:
        response = client.models.generate_content(
            model=target_model,
            contents=gemini_contents,
            config=_prepare_gemini_config(target_model)
        )
        content = response.text
        return {
            "response": content,
            "messages": [*messages, {"role": "assistant", "content": content}],
            "model": target_model,
        }
    except Exception as e:
        logger.error("Gemini chat failed: %s", e)
        return {
            "response": f"Error: {e}",
            "messages": messages, 
            "model": target_model
        }


@traceable(run_type="llm", name="Gemini Chat (Streaming)")
async def astream_chat_response(
    messages: List[ChatMessage],
    *,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Async generator for streaming responses from Gemini.
    """
    client = _build_gemini_client()
    target_model = model or DEFAULT_CHAT_MODEL
    
    gemini_contents = []
    for msg in messages:
        if msg["role"] == "system":
            continue
        role = "user" if msg["role"] == "user" else "model"
        gemini_contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    if not gemini_contents:
        gemini_contents.append(types.Content(role="user", parts=[types.Part(text="Hello")]))

    try:
        # Use simple iteration over the stream
        config = _prepare_gemini_config(target_model)
        response_stream = client.models.generate_content_stream(
            model=target_model,
            contents=gemini_contents,
            config=config
        )
        
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        logger.error("Gemini streaming failed: %s", e)
        yield f"[Error: {str(e)}]"


__all__ = [
    "ChatMessage", 
    "ChatResult", 
    "generate_chat_response", 
    "astream_chat_response", 
    "GENERAL_CHAT_SYSTEM_PROMPT"
]

