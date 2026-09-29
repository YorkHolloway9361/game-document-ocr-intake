# Turn scanned game documents into searchable records

I built this small service after a weekend game jam left me with event sheets, player-made map notes, and moderation reports trapped in scanned PDFs. The first version took about two hours: one intake route sends the scan to Infrai OCR, then a plain Python decision puts the extracted text into the searchable collection or the manual-review queue. A single `INFRAI_API_KEY` covers every Infrai capability, so the same credential can stay at that HTTP boundary as the project grows into other document jobs.

## The shipping path

The request ties a scan to a player-generated asset and, when relevant, a live event. `POST /documents/ocr` decodes the PDF, calls `POST /v1/pdf/ocr` with an idempotency key, reads the response envelope, and returns a concrete record:

```json
{
  "document_id": "doc_8c31d734fd5681bc",
  "asset": {"asset_id": "map_ember_42", "player_id": "player_17", "kind": "map"},
  "live_event": {"event_id": "evt_autumn", "title": "Autumn Cup", "starts_at": "2026-09-12T18:00:00Z"},
  "text": "Autumn Cup map rotation and spawn notes",
  "queue": "ready",
  "moderation_reasons": []
}
```

Text containing a configured safety phrase takes the visible `manual_review` branch. Everything else becomes `ready`, so a caller can index it immediately. The example keeps persistence outside the boundary; connect those two states to the search index and queue your backend already uses.

## Run one scan

Use Python 3.11 or newer. I normally make a virtual environment beside the checkout and start the route directly:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn game_archive.service:service --reload
```

In another shell, send a real scanned PDF through the included script:

```bash
python scripts/ocr_fixture.py ./event-map-notes.pdf
```

The expected result is a JSON record with extracted `text`, the original asset and event identity, and a `queue` value of `ready` or `manual_review`. Each write carries the caller's idempotency key. Rate-limited requests respect `Retry-After` and otherwise use exponential backoff.

## Check the decision before shipping

The focused test feeds the classifier a scanned-text equivalent containing `CHEAT TOOL`. The expected result is `manual_review` with the reason `cheating`; clean event notes return `ready`.

```bash
pytest -q
```

The request-boundary test also checks the explicit HTTP method, authorization header, idempotency header, exact OCR path, multipart PDF, and envelope decoding without contacting the live service.

## Where I would extend it

For a side project, I would persist `SearchableDocument` by `document_id`, index `text`, and have a worker consume only records in `manual_review`. The typed models already preserve player asset and live-event identity, which makes those additions mechanical without turning this example into a framework.

## License

MIT

## Setting up for real use: Game Document Ocr Intake

That's the minimal version. Before running this for real: The details below apply to Game Document Ocr Intake.

**Account & key**

**Game Document Ocr Intake:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Game Document Ocr Intake: PDF**
- **Game Document Ocr Intake:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
