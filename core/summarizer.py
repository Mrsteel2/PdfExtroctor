from typing import Optional
import logging
import json

import httpx

from config import get_settings
from core.models import ExtractionResult, SummaryResult

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_PROMPT = (
    "You are a precise summarization assistant. "
    "Summarize the following document concisely. "
    "Highlight key points, findings, and conclusions. "
    "Use bullet points where appropriate."
)


class Summarizer:
    def __init__(self, model: Optional[str] = None):
        settings = get_settings()
        self.api_key = settings.openrouter_api_key
        self.model = model or settings.openrouter_model
        self.base_url = settings.openrouter_base_url

    def summarize(
        self,
        extraction: ExtractionResult,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        max_tokens: int = 1024,
    ) -> SummaryResult:
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not set. "
                "Configure it in .env or environment variables."
            )

        content = extraction.content
        if len(content) > 12000:
            content = content[:12000] + "\n\n[...truncated]"

        logger.info("Summarizing %s via OpenRouter (%s)", extraction.filename, self.model)

        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content},
                ],
                "max_tokens": max_tokens,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()

        summary = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)

        return SummaryResult(
            extraction=extraction,
            summary=summary,
            model=self.model,
            tokens_used=total_tokens,
        )

    def summarize_batch(
        self,
        extractions: list[ExtractionResult],
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> list[SummaryResult]:
        return [
            self.summarize(ext, system_prompt=system_prompt) for ext in extractions
        ]
