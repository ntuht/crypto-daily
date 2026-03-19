"""
llm_wrapper.py — Lightweight LLM wrapper for the daily digest pipeline.

Provides the same interface as strategy/llm_backends.py but uses
google-genai directly. This module is committed to git and available
in CI (GitHub Actions).

Interface:
    llm = create_llm(config)   # config = {"api_key": ..., "model": ..., ...}
    llm.set_system_prompt(prompt)
    llm.reset_conversation()
    response_text = llm.query(user_prompt)
    print(llm.usage.summary())
"""

import os


class UsageTracker:
    """Track token usage."""
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.calls = 0

    def summary(self):
        return f"{self.calls} calls, {self.input_tokens} in / {self.output_tokens} out"


class GeminiWrapper:
    """Wrapper around google-genai for Gemini models."""

    def __init__(self, api_key, model="gemini-2.5-flash", temperature=0.3,
                 max_tokens=8192):
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = ""
        self.usage = UsageTracker()

    def set_system_prompt(self, prompt):
        self.system_prompt = prompt

    def reset_conversation(self):
        pass  # stateless per-call

    def query(self, user_prompt):
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt or None,
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            thinking_config=types.ThinkingConfig(
                thinking_budget=2048,
            ),
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=config,
        )

        self.usage.calls += 1
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            self.usage.input_tokens += getattr(meta, "prompt_token_count", 0)
            self.usage.output_tokens += getattr(meta, "candidates_token_count", 0)

        # Extract text from response parts (skip thinking parts)
        parts = []
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "thought") and part.thought:
                    continue
                if part.text:
                    parts.append(part.text)
        return "\n".join(parts)


def create_llm(config):
    """Create an LLM wrapper from config dict.

    config keys: api_key, model, temperature, max_tokens
    Falls back to GEMINI_API_KEY env var if api_key not in config.
    """
    api_key = config.get("api_key") or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("No API key found in config or GEMINI_API_KEY env var")

    return GeminiWrapper(
        api_key=api_key,
        model=config.get("model", "gemini-2.5-flash"),
        temperature=config.get("temperature", 0.3),
        max_tokens=config.get("max_tokens", 8192),
    )
