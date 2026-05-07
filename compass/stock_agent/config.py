"""
LLM endpoint configuration for stock agent.

Defaults to the local qwen3 endpoint that supports vision (image + text).
Override via environment variables or by passing a custom config dict.
"""

import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Configuration for the vision-capable LLM endpoint."""
    base_url: str = os.getenv("STOCK_AGENT_LLM_URL", "http://10.106.1.89:8080/v1")
    model: str = os.getenv("STOCK_AGENT_LLM_MODEL", "gpt-oss")  # matches your config
    api_key: str = os.getenv("STOCK_AGENT_LLM_API_KEY", "")  # empty for local
    max_tokens: int = int(os.getenv("STOCK_AGENT_MAX_TOKENS", "4096"))
    temperature: float = float(os.getenv("STOCK_AGENT_TEMPERATURE", "0.1"))

    # Override URL for OpenAI-compatible providers (Claude, GPT-4o, etc.)
    # e.g., "https://api.openai.com/v1" with model "gpt-4o"
    @classmethod
    def for_openai(cls, api_key: str, model: str = "gpt-4o") -> "LLMConfig":
        return cls(
            base_url="https://api.openai.com/v1",
            model=model,
            api_key=api_key,
        )

    @classmethod
    def for_anthropic(cls, api_key: str, model: str = "claude-sonnet-4-6") -> "LLMConfig":
        # Anthropic uses a different SDK, but we can still use
        # openai-compatible endpoint if proxying
        return cls(
            base_url="https://api.anthropic.com/v1",
            model=model,
            api_key=api_key,
        )
