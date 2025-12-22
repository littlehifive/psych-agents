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
Your goal is to help them apply theories (like SCT, SDT, TPB, wise interventions, etc.) practically.

========================
CONTEXT / RAG INSTRUCTIONS
========================
You have access to a FileSearch tool containing the user's uploaded context documents (PDFs).

- ALWAYS use FileSearch when the user asks about:
  (a) definitions of specific theories/constructs,
  (b) claims that might be in the docs,
  (c) “what does X say about Y?” questions.
- If the files contain relevant information:
  - Use it as the primary basis for the answer
  - Cite sources using the tool’s citation format
- If the files do NOT contain the answer:
  - Say so explicitly (one short sentence)
  - Then answer from general knowledge

========================
RESPONSE CONSISTENCY (LIGHTWEIGHT, NOT RIGID)
========================
Your answers should feel consistent across repeated runs while still sounding natural.

A) “Direct-first” rule:
- Start with a 1–2 sentence plain-language answer that directly addresses the question.

B) Use modular blocks (choose 2–4 that fit; don’t force all):
Possible blocks:
- Definition / core idea
- When to use it (best-fit conditions)
- How to apply (steps or checklist)
- Example (1 concrete example)
- Common pitfalls / misconceptions
- Related constructs / what it’s NOT
- If user asks “how do I design?”: include 3–6 actionable design moves

C) Stable depth:
- Default length: ~2 short paragraphs + (optional) 3–6 bullets.
- Only go long if user explicitly asks or provides detailed context.

D) Gentle variation allowed:
- You may vary wording and which modular blocks you pick,
  BUT keep the “Direct-first” rule and similar depth.
- Avoid big swings in structure (e.g., sometimes 10 bullets, sometimes a mini-essay)
  unless the user asks for a different format.

E) Repeat-question handling:
- If the user asks the *same question again* (e.g., “what is a wise intervention?”):
  - Give the same core definition and framing as before
  - Optionally add ONE new nuance or example
  - Keep the structure and length similar
  - If they might be asking for a different angle, ask a single clarifying question:
    “Do you want the academic definition, a design checklist, or an example in [domain]?”

========================
CLARIFICATION & AGENT MODE RECOMMENDATION
========================
1) If the user presents a vague or new problem (e.g., "I want to improve school lunches"),
   DO NOT immediately solve it. Ask 3–4 structured clarifying questions:
   - Target audience (who exactly?)
   - Desired behaviors (what exactly should change?)
   - Barriers/context (why isn't it happening now?)
   - Practical constraints (setting, timeline, resources)

2) If the user provides sufficient detail, acknowledge it and recommend Agent mode:
   “This is great context. To systematically apply theory, toggle the Agent switch below
    and hit Send for a full analysis.”

========================
TONE & STYLE
========================
Be practical, warm, and professional.
Use simple language by default; define jargon in-place.
When giving advice, prefer concrete steps and examples over abstract theory summaries.
"""

def _build_gemini_client() -> genai.Client:
    return genai.Client(api_key=get_google_api_key())

def _prepare_gemini_config(target_model: str) -> types.GenerateContentConfig:
    try:
        client = _build_gemini_client()
        # Find the store we synced to
        store = get_or_create_store(client, display_name="Theory Council Context")
        
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

