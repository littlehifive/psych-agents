"""
FastAPI server that exposes a lightweight RAG chat endpoint.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4
from functools import partial

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from theory_council.chat import ChatMessage as ChatMessageDict, astream_chat_response, organize_library_item
from theory_council.config import get_langsmith_settings

logger = logging.getLogger("theory_council.server")
logging.basicConfig(level=logging.INFO)

# In-memory store for Library items
class LibraryItem(BaseModel):
    id: str
    question: str
    answer: str
    citations: Optional[str] = None
    title: str
    summary: str
    theme: str
    tags: List[str]
    createdAt: int

LIBRARY: List[LibraryItem] = []

langsmith_settings = get_langsmith_settings()
for key, value in langsmith_settings.items():
    if value and not os.environ.get(key):
        os.environ[key] = value
        logger.debug("Configured %s for LangSmith observability.", key)

if langsmith_settings.get("LANGCHAIN_API_KEY") and not os.environ.get("LANGCHAIN_TRACING_V2"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

app = FastAPI(
    title="Agentic Researcher API",
    description="Lightweight RAG chat for agency-based intervention design.",
    version="0.1.0",
)

@app.on_event("startup")
async def startup_event():
    try:
        from theory_council.gemini_store import sync_all_theory_stores
        
        # Determine context dir relative to this file
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        CONTEXT_DIR = os.path.join(PROJECT_ROOT, "context")

        if os.environ.get("GOOGLE_API_KEY"):
            logger.info("Syncing Gemini File Search Stores...")
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, partial(sync_all_theory_stores, CONTEXT_DIR))
        else:
            logger.info("GOOGLE_API_KEY not set, skipping Gemini RAG sync.")
            
    except Exception as e:
        logger.error("Failed to sync Gemini store on startup: %s", e)

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


class ChatMessageModel(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

    def to_dict(self) -> ChatMessageDict:
        return {"role": self.role, "content": self.content}


class ConversationRequest(BaseModel):
    messages: List[ChatMessageModel]
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = Field(
        default=None,
        description="Conversation/session identifier.",
    )

class LibraryCreateRequest(BaseModel):
    question: str
    answer: str
    citations: Optional[str] = None

class LibraryUpdateRequest(BaseModel):
    title: Optional[str] = None
    theme: Optional[str] = None
    tags: Optional[List[str]] = None

def _format_sse(event: str, payload: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/conversation/send/stream")
async def stream_conversation_endpoint(payload: ConversationRequest) -> StreamingResponse:
    session_id = payload.session_id or uuid4().hex
    user_msg_dict = [msg.to_dict() for msg in payload.messages]

    async def event_stream():
        # Yield session ID immediately
        yield _format_sse("started", {"session_id": session_id})

        full_content = ""
        try:
            async for chunk in astream_chat_response(
                user_msg_dict, 
                metadata=payload.metadata
            ):
                full_content += chunk
                yield _format_sse("token", {"chunk": chunk})
            
            # Record final assistant message
            assistant_message: ChatMessageModel = ChatMessageModel(role="assistant", content=full_content)
            
            # Yield completion event with the full message object
            yield _format_sse("complete", {
                "session_id": session_id,
                "message": assistant_message.model_dump()
            })

        except Exception as e:
            logger.error(f"Chat stream failed: {e}")
            yield _format_sse("error", {"detail": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/library", response_model=List[LibraryItem])
def list_library():
    return LIBRARY

@app.post("/library", response_model=LibraryItem)
async def create_library_item(payload: LibraryCreateRequest):
    import time
    # Call Gemini to organize
    try:
        org_data = organize_library_item(payload.question, payload.answer, payload.citations)
    except Exception as e:
        logger.error(f"Failed to organize library item: {e}")
        org_data = {
            "title": payload.question[:50],
            "summary": payload.answer[:200],
            "theme": "Other",
            "tags": ["saved"]
        }
    
    item = LibraryItem(
        id=uuid4().hex,
        question=payload.question,
        answer=payload.answer,
        citations=payload.citations,
        title=org_data.get("title", "Saved Response"),
        summary=org_data.get("summary", ""),
        theme=org_data.get("theme", "Other"),
        tags=org_data.get("tags", []),
        createdAt=int(time.time() * 1000)
    )
    
    LIBRARY.append(item)
    return item

@app.delete("/library/{item_id}")
def delete_library_item(item_id: str):
    global LIBRARY
    LIBRARY = [item for item in LIBRARY if item.id != item_id]
    return {"status": "ok"}

@app.patch("/library/{item_id}", response_model=LibraryItem)
def update_library_item(item_id: str, payload: LibraryUpdateRequest):
    for item in LIBRARY:
        if item.id == item_id:
            if payload.title is not None: item.title = payload.title
            if payload.theme is not None: item.theme = payload.theme
            if payload.tags is not None: item.tags = payload.tags
            return item
    raise HTTPException(status_code=404, detail="Item not found")


__all__ = ["app"]
