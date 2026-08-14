from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Iterator

import httpx

from backend.core.config import get_settings


_DISABLED_PROVIDERS = {
    "",
    "disabled",
    "none",
    "off",
}

_PROVIDER_DEFAULTS = {
    "deepseek": {
        "base_url":
            "https://api.deepseek.com",
        "model":
            "deepseek-v4-flash",
    },
    "groq": {
        "base_url":
            "https://api.groq.com/openai/v1",
        "model":
            "",
    },
}


class LLMStreamError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    base_url: str
    api_key: str
    model: str


@dataclass
class LLMResult:
    enabled: bool
    answer: str | None
    provider: str
    model: str | None = None
    error: str | None = None


class LLMService:
    """OpenAI Chat Completions compatible provider adapter.

    Retrieval decides what context is allowed. This service only generates a
    final answer from approved RAG context.

    Named providers:
    - deepseek
    - groq

    Generic OpenAI-compatible providers can still use:
    LLM_PROVIDER, LLM_BASE_URL, LLM_API_KEY, and LLM_MODEL.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def _provider_config(
        self,
    ) -> ProviderConfig:
        provider = (
            self.settings.llm_provider
            or "disabled"
        ).lower().strip()

        defaults = _PROVIDER_DEFAULTS.get(
            provider,
            {},
        )

        configured_base_url = (
            self.settings.llm_base_url
            or ""
        ).strip()

        configured_model = (
            self.settings.llm_model
            or ""
        ).strip()

        base_url = (
            configured_base_url
            or defaults.get(
                "base_url",
                "",
            )
        ).rstrip("/")

        model = (
            configured_model
            or defaults.get(
                "model",
                "",
            )
        )

        generic_key = (
            self.settings.llm_api_key
            or ""
        ).strip()

        if provider == "deepseek":
            api_key = (
                self.settings.deepseek_api_key
                or generic_key
            ).strip()
        elif provider == "groq":
            api_key = (
                self.settings.groq_api_key
                or generic_key
            ).strip()
        else:
            api_key = generic_key

        return ProviderConfig(
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model=model,
        )

    def is_enabled(self) -> bool:
        config = self._provider_config()

        return (
            config.provider
            not in _DISABLED_PROVIDERS
            and bool(config.api_key)
            and bool(config.base_url)
            and bool(config.model)
        )

    @staticmethod
    def _max_tokens() -> int:
        raw = os.getenv(
            "LLM_MAX_TOKENS",
            "500",
        )

        try:
            value = int(raw)
        except ValueError:
            value = 500

        return max(
            64,
            min(
                4096,
                value,
            ),
        )

    @staticmethod
    def _safe_http_error(
        provider: str,
        status_code: int,
    ) -> str:
        if status_code == 401:
            return (
                f"{provider} authentication failed "
                "(HTTP 401). Check the API key."
            )

        if status_code == 402:
            return (
                f"{provider} reported insufficient "
                "account balance (HTTP 402)."
            )

        if status_code == 404:
            return (
                f"{provider} endpoint or model was "
                "not found (HTTP 404)."
            )

        if status_code == 422:
            return (
                f"{provider} rejected one or more "
                "request parameters (HTTP 422)."
            )

        if status_code == 429:
            return (
                f"{provider} rate limit was reached "
                "(HTTP 429)."
            )

        if status_code >= 500:
            return (
                f"{provider} is temporarily unavailable "
                f"(HTTP {status_code})."
            )

        return (
            f"{provider} request failed "
            f"(HTTP {status_code})."
        )

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You are a safe assistant for an ophthalmology screening "
            "and appointment platform. "
            "Answer using ONLY the provided context. "
            "Never invent database records, appointment times, diagnoses, "
            "or doctors. "
            "Do not provide a final medical diagnosis. "
            "Use clear Markdown. "
            "When answering Arabic, use natural Arabic with short paragraphs "
            "and bullet points. "
            "When the answer mixes Arabic and English terms, keep terms "
            "readable and avoid broken tables. "
            "Prefer bullet lists over Markdown tables. "
            "If context is insufficient, say so clearly."
        )

    def _payload(
        self,
        question: str,
        context: str,
        *,
        stream: bool,
    ) -> dict:
        config = self._provider_config()

        payload: dict = {
            "model":
                config.model,
            "messages": [
                {
                    "role":
                        "system",
                    "content":
                        self._system_prompt(),
                },
                {
                    "role":
                        "user",
                    "content": (
                        f"Context:\n{context}\n\n"
                        f"Question:\n{question}\n\n"
                        "Write a concise, well-formatted answer. "
                        "Use the same main language as the user."
                    ),
                },
            ],
            "temperature":
                0.2,
            "stream":
                stream,
            "max_tokens":
                self._max_tokens(),
        }

        # DeepSeek V4 thinking mode defaults to enabled. This final RAG
        # synthesis step intentionally uses non-thinking mode for lower
        # latency and deterministic use of the configured temperature.
        if config.provider == "deepseek":
            payload["thinking"] = {
                "type":
                    "disabled",
            }

        return payload

    @staticmethod
    def _headers(
        config: ProviderConfig,
    ) -> dict[str, str]:
        return {
            "Authorization":
                f"Bearer {config.api_key}",
            "Content-Type":
                "application/json",
        }

    def answer_with_context(
        self,
        question: str,
        context: str,
    ) -> LLMResult:
        config = self._provider_config()

        if not self.is_enabled():
            return LLMResult(
                enabled=False,
                answer=None,
                provider=config.provider,
                model=config.model or None,
            )

        url = (
            f"{config.base_url}"
            "/chat/completions"
        )

        try:
            with httpx.Client(
                timeout=httpx.Timeout(
                    70.0
                ),
            ) as client:
                response = client.post(
                    url,
                    headers=self._headers(
                        config
                    ),
                    json=self._payload(
                        question,
                        context,
                        stream=False,
                    ),
                )

            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            status_code = (
                exc.response.status_code
            )

            return LLMResult(
                enabled=True,
                answer=None,
                provider=config.provider,
                model=config.model,
                error=self._safe_http_error(
                    config.provider,
                    status_code,
                ),
            )

        except httpx.RequestError:
            return LLMResult(
                enabled=True,
                answer=None,
                provider=config.provider,
                model=config.model,
                error=(
                    f"Could not reach "
                    f"{config.provider}."
                ),
            )

        try:
            data = response.json()
            choices = data.get(
                "choices"
            )

            if (
                not isinstance(
                    choices,
                    list,
                )
                or not choices
            ):
                raise ValueError(
                    "Missing choices."
                )

            message = choices[0].get(
                "message"
            )

            if not isinstance(
                message,
                dict,
            ):
                raise ValueError(
                    "Missing message."
                )

            content = message.get(
                "content"
            )

            if not isinstance(
                content,
                str,
            ):
                raise ValueError(
                    "Missing answer content."
                )

            answer = content.strip()

            if not answer:
                raise ValueError(
                    "Empty answer content."
                )

        except (
            ValueError,
            TypeError,
            KeyError,
        ):
            return LLMResult(
                enabled=True,
                answer=None,
                provider=config.provider,
                model=config.model,
                error=(
                    f"{config.provider} returned "
                    "an invalid response."
                ),
            )

        return LLMResult(
            enabled=True,
            answer=answer,
            provider=config.provider,
            model=config.model,
            error=None,
        )

    def stream_answer_with_context(
        self,
        question: str,
        context: str,
    ) -> Iterator[str]:
        """Yield visible answer text as the provider sends SSE deltas."""

        config = self._provider_config()

        if not self.is_enabled():
            return

        url = (
            f"{config.base_url}"
            "/chat/completions"
        )

        try:
            with httpx.Client(
                timeout=httpx.Timeout(
                    70.0
                ),
            ) as client:
                with client.stream(
                    "POST",
                    url,
                    headers=self._headers(
                        config
                    ),
                    json=self._payload(
                        question,
                        context,
                        stream=True,
                    ),
                ) as response:
                    response.raise_for_status()

                    for line in (
                        response.iter_lines()
                    ):
                        if not line:
                            continue

                        # DeepSeek can emit SSE keep-alive comments.
                        if line.startswith(":"):
                            continue

                        if not line.startswith(
                            "data:"
                        ):
                            continue

                        body = (
                            line[5:]
                            .strip()
                        )

                        if body == "[DONE]":
                            break

                        try:
                            data = json.loads(
                                body
                            )
                        except json.JSONDecodeError:
                            continue

                        choices = (
                            data.get(
                                "choices"
                            )
                            or []
                        )

                        if not choices:
                            continue

                        delta = (
                            choices[0].get(
                                "delta"
                            )
                            or {}
                        )

                        content = (
                            delta.get(
                                "content"
                            )
                        )

                        if content:
                            yield str(
                                content
                            )

        except httpx.HTTPStatusError as exc:
            raise LLMStreamError(
                self._safe_http_error(
                    config.provider,
                    exc.response.status_code,
                )
            ) from exc

        except httpx.RequestError as exc:
            raise LLMStreamError(
                f"Could not reach "
                f"{config.provider}."
            ) from exc
