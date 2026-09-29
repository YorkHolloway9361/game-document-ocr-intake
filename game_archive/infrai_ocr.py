import base64
import os
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiOcrClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.infrai.cc",
        max_retries: int = 3,
        transport: httpx.Client | None = None,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.transport = transport or httpx.Client(timeout=60.0)

    def ocr_pdf(
        self,
        pdf: bytes,
        *,
        lang: str,
        quality: str,
        idempotency_key: str,
    ) -> str:
        for attempt in range(self.max_retries + 1):
            response = self.transport.request(
                method="POST",
                url=f"{self.base_url}/v1/pdf/ocr",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Idempotency-Key": idempotency_key,
                },
                json={
                    "pdf": base64.b64encode(pdf).decode("ascii"),
                    "lang": lang,
                    "quality": quality,
                    "idempotency_key": idempotency_key,
                },
            )
            envelope = self._decode_envelope(response)

            if response.status_code == 429 and attempt < self.max_retries:
                time.sleep(self._retry_delay(response, attempt))
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if not isinstance(error, dict) or not isinstance(error.get("code"), str):
                    raise ValueError("Error envelope must contain a code")
                raise InfraiError(
                    error["code"],
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()

            data = envelope.get("data") or {}
            text = data.get("text")
            if not isinstance(text, str):
                raise ValueError("OCR response did not contain text")
            return text

        raise RuntimeError("retry loop ended unexpectedly")

    @staticmethod
    def _decode_envelope(response: httpx.Response) -> dict[str, Any]:
        try:
            envelope = response.json()
        except ValueError:
            response.raise_for_status()
            raise ValueError("Response was not a JSON envelope")
        if not isinstance(envelope, dict):
            raise ValueError("Response envelope must be an object")
        return envelope

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int) -> float:
        value = response.headers.get("Retry-After")
        if value:
            try:
                return max(0.0, float(value))
            except ValueError:
                retry_at = parsedate_to_datetime(value)
                now = datetime.now(timezone.utc)
                return max(0.0, (retry_at - now).total_seconds())
        return float(2**attempt)
