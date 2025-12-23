"""
RAG utilities for the Theory Council.
Handles PDF ingestion, vector store creation, and context retrieval.
"""
from __future__ import annotations

import os
import shutil
from typing import List, Optional, TypedDict

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.vectorstores import Chroma
# from langchain_openai import OpenAIEmbeddings # Removed
from langchain_google_genai import GoogleGenerativeAIEmbeddings # Added
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import get_langsmith_settings, get_google_api_key

# Paths
# Assuming the code is running from project root or src/..
# We'll try to find the context folder relative to this file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
CONTEXT_DIR = os.path.join(PROJECT_ROOT, "context")
DB_DIR = os.path.join(PROJECT_ROOT, ".chroma_db")

class RetrievedChunk(TypedDict):
    content: str
    source: str
    page: int

def _get_embeddings():
    api_key = get_google_api_key()
    return GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=api_key)

def build_index(force_refresh: bool = False):
    """
    Ingest PDFs from the context directory and build/update the ChromaDB index.
    """
    if force_refresh and os.path.exists(DB_DIR):
        print(f"Removing existing DB at {DB_DIR}...")
        shutil.rmtree(DB_DIR)

    if os.path.exists(DB_DIR) and not force_refresh:
        print("Vector store already exists. Skipping ingestion (use force_refresh=True to rebuild).")
        return

    print(f"Loading PDFs from {CONTEXT_DIR}...")
    loader = DirectoryLoader(CONTEXT_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader, show_progress=True)
    documents = loader.load()

    if not documents:
        print("No PDF documents found in context directory.")
        return

    print(f"Loaded {len(documents)} document pages.")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True,
    )
    splits = text_splitter.split_documents(documents)
    print(f"Split into {len(splits)} chunks.")

    print("Creating vector store...")
    Chroma.from_documents(
        documents=splits,
        embedding=_get_embeddings(),
        persist_directory=DB_DIR,
        collection_name="theory_context"
    )
    print("Vector store created and persisted.")

def query_context(query: str, k: int = 4) -> List[RetrievedChunk]:
    """
    Search the vector store for context relevant to the query.
    """
    if not os.path.exists(DB_DIR):
        print("Warning: Vector store not found. Returning empty context.")
        return []

    vectorstore = Chroma(
        persist_directory=DB_DIR,
        embedding_function=_get_embeddings(),
        collection_name="theory_context"
    )
    
    results = vectorstore.similarity_search(query, k=k)
    
    retrieved: List[RetrievedChunk] = []
    for doc in results:
        retrieved.append({
            "content": doc.page_content,
            "source": os.path.basename(doc.metadata.get("source", "")),
            "page": doc.metadata.get("page", 0) + 1, # 1-indexed
        })
        
    return retrieved

def format_context_for_prompt(chunks: List[RetrievedChunk]) -> str:
    """
    Format retrieved chunks into a string for the LLM system prompt.
    """
    if not chunks:
        return ""
    
    formatted = ["RELEVANT THEORY CONTEXT (from uploaded documents):"]
    for i, chunk in enumerate(chunks, 1):
        formatted.append(f"--- SOURCE {i} ({chunk['source']}, p.{chunk['page']}) ---")
        formatted.append(f"\"{chunk['content']}\"")
    
    return "\n\n".join(formatted)

if __name__ == "__main__":
    # Allow running this script directly to build the index
    import sys
    # Hack to allow importing config if run adjacent to module
    sys.path.append(PROJECT_ROOT)
    
    print("Starting ingestion...")
    build_index(force_refresh=True)
    print("Ingestion complete.")
    
    # Simple test
    print("\nTesting retrieval for 'self-efficacy':")
    results = query_context("How does self-efficacy influence behavior?")
    for res in results:
        print(f" - [{res['source']} p.{res['page']}]: {res['content'][:100]}...")
