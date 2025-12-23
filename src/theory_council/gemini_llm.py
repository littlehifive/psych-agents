"""
Gemini Adapter for LangChain-style invocation.
Allows substituting ChatOpenAI with Google Gemini in the Theory Council graph.
"""
import logging
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types

from .config import get_google_api_key

logger = logging.getLogger("theory_council.gemini_llm")

class GeminiResponse:
    """
    Duck-typed response object compatible with LangChain's AIMessage.
    """
    def __init__(self, content: str):
        self.content = content

class GeminiLCWrapper:
    """
    A lightweight wrapper around google-genai to mimic ChatOpenAI's invoke method.
    """
    def __init__(self, model: str = "gemini-2.5-flash", store_name: Optional[str] = None, temperature: float = 0.3):
        self.model = model
        self.store_name = store_name
        self.temperature = temperature
        self.client = genai.Client(api_key=get_google_api_key())

    def _prepare_config(self) -> types.GenerateContentConfig:
        tools = []
        if self.store_name:
            tools = [
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[self.store_name]
                    )
                )
            ]
        
        return types.GenerateContentConfig(
            tools=tools,
            temperature=self.temperature,
            # We can also put system instruction here if we extract it, 
            # but the graph passes it as the first message.
        )

    def invoke(self, messages: List[Dict[str, str]]) -> GeminiResponse:
        """
        Mimics langchain_openai.ChatOpenAI.invoke
        messages: List of {"role": "system"|"user"|"assistant", "content": str}
        """
        gemini_contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                # Gemini 1.5/2.0 prefers system_instruction in config, 
                # but depending on SDK version we might need to be careful.
                # If we have multiple system messages, we join them.
                if system_instruction is None:
                    system_instruction = content
                else:
                    system_instruction += "\n\n" + content
            elif role == "user":
                gemini_contents.append(types.Content(role="user", parts=[types.Part(text=content)]))
            elif role == "assistant":
                gemini_contents.append(types.Content(role="model", parts=[types.Part(text=content)]))
        
        # Fallback if no user message (shouldn't happen in our graph)
        if not gemini_contents:
            gemini_contents.append(types.Content(role="user", parts=[types.Part(text="Hello")]))

        config = self._prepare_config()
        if system_instruction:
            config.system_instruction = system_instruction

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=gemini_contents,
                config=config
            )
            return GeminiResponse(content=response.text)
        except Exception as e:
            logger.error("Gemini invocation failed: %s", e)
            return GeminiResponse(content=f"Error generating response: {e}")
