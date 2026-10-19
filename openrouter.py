"""Minimal OpenRouter client using the OpenAI-compatible chat API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
import json
import time
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from costs import as_decimal

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ModelInfo:
    requested_id: str
    model_id: str
    name: str
    prompt_rate_usd_per_million: Decimal | None
    completion_rate_usd_per_million: Decimal | None
    pricing_source: str
    pricing_retrieved_at: str
    supported_parameters: tuple[str, ...]


class OpenRouterError(RuntimeError):
    """Sanitized provider/transport error, suitable for a result log."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retryable: bool = False,
        may_have_been_billed: bool = True,
        response_payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable
        self.may_have_been_billed = may_have_been_billed
        # Structured provider error/usage data can be logged without including
        # request headers or the API key.
        self.response_payload = response_payload


class OpenRouterClient:
    """OpenRouter API client. API key is held in memory and never serialized."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 90.0,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("an OpenRouter API key is required")
        self._api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._opener = opener
        self._models_cache: list[dict[str, Any]] | None = None

    def _open(self, request: Request):
        if self._opener is not None:
            return self._opener(request, timeout=self.timeout)
        return urlopen(request, timeout=self.timeout)

    def _request_json(
        self, method: str, path: str, payload: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=headers, method=method.upper())
        try:
            with self._open(request) as response:
                raw = response.read()
        except HTTPError as exc:
            status = int(exc.code)
            body = exc.read()
            try:
                parsed_body = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                parsed_body = None
            retryable = status in {408, 409, 425, 429, 500, 502, 503, 504, 524, 529}
            may_be_billed = status >= 500 or status in {408, 409, 425, 429}
            raise OpenRouterError(
                f"OpenRouter returned HTTP {status}",
                status_code=status,
                retryable=retryable,
                may_have_been_billed=may_be_billed,
                response_payload=parsed_body if isinstance(parsed_body, dict) else None,
            ) from None
        except (URLError, TimeoutError, OSError) as exc:
            # The request may have reached OpenRouter before the connection
            # failed; conservatively preserve the spend as unknown.
            reason = getattr(exc, "reason", None)
            safe_reason = type(reason).__name__ if reason is not None else type(exc).__name__
            raise OpenRouterError(
                f"OpenRouter transport error ({safe_reason})",
                retryable=True,
                may_have_been_billed=True,
            ) from None

        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise OpenRouterError(
                "OpenRouter returned a non-JSON response",
                retryable=True,
                may_have_been_billed=True,
            ) from None
        if not isinstance(result, dict):
            raise OpenRouterError(
                "OpenRouter returned an unexpected JSON response",
                retryable=True,
                may_have_been_billed=True,
            )
        return result

    def list_models(self, *, refresh: bool = False) -> list[dict[str, Any]]:
        if self._models_cache is not None and not refresh:
            return self._models_cache
        payload = self._request_json("GET", "/models")
        rows = payload.get("data")
        if not isinstance(rows, list):
            raise OpenRouterError("OpenRouter model catalog has no data list")
        self._models_cache = [row for row in rows if isinstance(row, dict)]
        return self._models_cache

    @staticmethod
    def _price_per_million(raw_price: Any) -> Decimal | None:
        per_token = as_decimal(raw_price)
        if per_token is None:
            return None
        return per_token * Decimal(1_000_000)

    def resolve_model(self, requested_id: str) -> ModelInfo:
        if not requested_id or not requested_id.strip():
            raise ValueError("model ID must not be empty")
        model_name = requested_id.strip()
        models = self.list_models()
        exact = [row for row in models if row.get("id") == model_name]
        if not exact and "/" not in model_name:
            # Accept a short model name only when the catalog has one exact
            # final-segment match; never guess among variants or batch models.
            exact = [
                row
                for row in models
                if str(row.get("id", "")).rsplit("/", 1)[-1] == model_name
            ]
        if len(exact) != 1:
            if not exact:
                raise ValueError(f"OpenRouter model not found: {model_name}")
            ids = ", ".join(str(row.get("id")) for row in exact[:5])
            raise ValueError(
                f"OpenRouter model name '{model_name}' is ambiguous; use a full ID: {ids}"
            )

        row = exact[0]
        pricing = row.get("pricing") if isinstance(row.get("pricing"), dict) else {}
        supported = row.get("supported_parameters")
        supported_parameters = (
            tuple(str(value) for value in supported)
            if isinstance(supported, list)
            else ()
        )
        return ModelInfo(
            requested_id=model_name,
            model_id=str(row.get("id")),
            name=str(row.get("name") or row.get("id")),
            prompt_rate_usd_per_million=self._price_per_million(
                pricing.get("prompt")
            ),
            completion_rate_usd_per_million=self._price_per_million(
                pricing.get("completion")
            ),
            pricing_source="OpenRouter /models catalog (uncached rates)",
            pricing_retrieved_at=utc_now(),
            supported_parameters=supported_parameters,
        )

    @staticmethod
    def validate_reasoning_effort(model: ModelInfo, effort: str | None) -> None:
        if effort is None:
            return
        if effort not in {"low", "medium", "high"}:
            raise ValueError("reasoning effort must be low, medium or high")
        supported = set(model.supported_parameters)
        if supported and not ({"reasoning_effort", "reasoning"} & supported):
            raise ValueError(
                f"model {model.model_id} does not advertise reasoning-effort support"
            )

    def complete(
        self,
        model_id: str,
        prompt: str,
        *,
        reasoning_effort: str | None = None,
        max_completion_tokens: int = 512,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "max_completion_tokens": max_completion_tokens,
        }
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort
        response = self._request_json("POST", "/chat/completions", payload)
        error = response.get("error")
        choices = response.get("choices")
        choice_error = None
        if isinstance(choices, list) and choices and isinstance(choices[0], dict):
            choice_error = choices[0].get("error")
        provider_error = error if isinstance(error, dict) else (
            choice_error if isinstance(choice_error, dict) else None
        )
        if provider_error is not None:
            try:
                status = int(provider_error.get("code"))
            except (TypeError, ValueError):
                status = None
            retryable = status in {408, 409, 425, 429, 500, 502, 503, 504, 524, 529}
            raise OpenRouterError(
                "OpenRouter returned a structured provider error",
                status_code=status,
                retryable=retryable,
                may_have_been_billed=(status is None or status >= 500 or status in {408, 409, 425, 429}),
                response_payload=response,
            )
        # A successful HTTP response without choices/error is treated as an
        # invalid model response by the parser; it is not re-queried.
        return response

    def generation_details(
        self, generation_id: str, *, max_attempts: int = 3, retry_delay: float = 0.5
    ) -> dict[str, Any]:
        if not generation_id:
            raise ValueError("generation ID must not be empty")
        query = urlencode({"id": generation_id})
        for attempt in range(max_attempts):
            try:
                return self._request_json("GET", f"/generation?{query}")
            except OpenRouterError as exc:
                # OpenRouter documents that generation metadata can appear a
                # few seconds after the completion response. Retry only the
                # free metadata lookup on a 404; never repeat inference here.
                if exc.status_code != 404 or attempt + 1 >= max_attempts:
                    raise
                if retry_delay:
                    time.sleep(retry_delay * (attempt + 1))
        raise OpenRouterError("generation metadata was not available")
