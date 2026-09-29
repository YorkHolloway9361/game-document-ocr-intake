import base64
import json

import httpx

from game_archive.infrai_ocr import InfraiOcrClient


def test_ocr_request_uses_pdf_fields_and_reads_envelope() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/pdf/ocr"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert request.headers["Idempotency-Key"] == "intake-0001"
        assert request.headers["Content-Type"] == "application/json"
        assert json.loads(request.content) == {
            "pdf": base64.b64encode(b"%PDF-scan").decode("ascii"),
            "lang": "eng",
            "quality": "high",
            "idempotency_key": "intake-0001",
        }
        return httpx.Response(200, json={"ok": True, "data": {"text": "Spawn rules"}, "error": None, "metadata": {}})

    transport = httpx.Client(transport=httpx.MockTransport(handler))
    client = InfraiOcrClient(api_key="test-key", transport=transport)

    assert client.ocr_pdf(b"%PDF-scan", lang="eng", quality="high", idempotency_key="intake-0001") == "Spawn rules"
