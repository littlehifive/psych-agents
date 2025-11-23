"""
Environment loading and LLM helpers for the Theory Council project.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Allow project-local .env values to override inherited environment entries
load_dotenv(override=True)

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.35
INTEGRATOR_MODEL = os.environ.get("INTEGRATOR_MODEL", "gpt-4.1")
INTEGRATOR_TEMPERATURE = 0.4


def _require_openai_key() -> str:
    """
    Ensure that OPENAI_API_KEY is available and return it.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Please configure it in your environment or .env file.")
    return api_key


def get_llm(model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE) -> ChatOpenAI:
    """
    Build a ChatOpenAI instance with the provided parameters.
    """
    api_key = _require_openai_key()
    return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)


def get_integrator_llm(
    model: Optional[str] = None,
    temperature: float = INTEGRATOR_TEMPERATURE,
) -> ChatOpenAI:
    """
    Return a ChatOpenAI instance tailored for the Integrator agent.
    """
    resolved_model = model or INTEGRATOR_MODEL
    return get_llm(model=resolved_model, temperature=temperature)


def get_langsmith_settings() -> Dict[str, Optional[str]]:
    """
    Surface optional LangSmith-related environment variables for observability tooling.
    """
    return {
        "LANGCHAIN_TRACING_V2": os.environ.get("LANGCHAIN_TRACING_V2"),
        "LANGCHAIN_API_KEY": os.environ.get("LANGCHAIN_API_KEY"),
        "LANGCHAIN_ENDPOINT": os.environ.get("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"),
        "LANGCHAIN_PROJECT": os.environ.get("LANGCHAIN_PROJECT"),
    }

