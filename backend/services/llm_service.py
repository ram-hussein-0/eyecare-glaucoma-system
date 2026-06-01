from __future__ import annotations

from dataclasses import dataclass

import httpx

from backend.core.config import get_settings


@dataclass
class LLMResult:
    enabled: bool
    answer: str | None
    provider: str
    model: str | None = None


class LLMService:
    """OpenAI-compatible LLM adapter.

    RAG/database retrieval decides what context is allowed.
    This service only formats the final answer from approved context.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_enabled(self) -> bool:
        provider = (self.settings.llm_provider or "disabled").lower().strip()
        return provider not in {"", "disabled", "none", "off"} and bool(self.settings.llm_api_key)

    def answer_with_context(self, question: str, context: str) -> LLMResult:
        provider = (self.settings.llm_provider or "disabled").lower().strip()
        if not self.is_enabled():
            return LLMResult(enabled=False, answer=None, provider=provider)

        base_url = self.settings.llm_base_url.rstrip("/")
        url = f"{base_url}/chat/completions"

        system_prompt = (
            "You are a safe assistant for an ophthalmology screening and appointment platform. "
            "Answer using ONLY the provided context. Never invent database records, appointment times, diagnoses, or doctors. "
            "Do not provide a final medical diagnosis. Use clear Markdown. "
            "When answering Arabic, use natural Arabic with short paragraphs and bullet points. "
            "When the answer mixes Arabic and English terms, keep terms readable and avoid broken tables. "
            "Prefer bullet lists over markdown tables. "
            "If context is insufficient, say so clearly."
        )

        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Context:\n{context}\n\n"
                        f"Question:\n{question}\n\n"
                        "Write a concise, well-formatted answer. Use the same main language as the user."
                    ),
                },
            ],
            "temperature": 0.2,
        }

        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=70)
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            return LLMResult(
                enabled=True,
                answer=str(answer).strip(),
                provider=provider,
                model=self.settings.llm_model,
            )
        except Exception as exc:
            return LLMResult(
                enabled=True,
                answer=f"The language model provider is configured but failed to respond: {exc}",
                provider=provider,
                model=self.settings.llm_model,
            )
