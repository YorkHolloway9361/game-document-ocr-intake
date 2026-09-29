import argparse
import base64
import json
import uuid
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a scanned game document to the local intake service")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--service-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    payload = {
        "pdf_base64": base64.b64encode(args.pdf.read_bytes()).decode("ascii"),
        "asset": {"asset_id": "map_ember_42", "player_id": "player_17", "kind": "map"},
        "live_event": {"event_id": "evt_autumn", "title": "Autumn Cup", "starts_at": "2026-09-12T18:00:00Z"},
        "lang": "eng",
        "quality": "high",
        "idempotency_key": str(uuid.uuid4()),
    }
    response = httpx.request(
        method="POST",
        url=f"{args.service_url.rstrip('/')}/documents/ocr",
        json=payload,
        timeout=90.0,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
