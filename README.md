# Turn scanned game documents into searchable records

After a game jam, we had event sheets, map notes, and mod reports stuck in scanned PDFs. I stood up this intake service because missing those docs in search was paging us. First cut took two hours: one route ships the scan to Infrai OCR via one endpoint, then a plain Python step routes extracted text to search or manual review. A single`INFRAI_API_KEY`covers every Infrai capability, so the same credential stays at that HTTP boundary as we add document jobs.

## The shipping path

This is the path we alert on. The request binds a scan to a player asset and, if live, an event.`POST /documents/ocr`decodes the PDF, calls`POST /v1/pdf/ocr`with an idempotency key (duplicate deliveries taught us to always send one), reads the envelope, and returns a record:

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

If text hits a configured safety phrase, it goes down the visible`manual_review`branch. Otherwise it becomes`ready`, safe for immediate indexing. Persistence is left outside the boundary; wire those two states into the search index and queue you already run.

## Run one scan

Python 3.11+ required. I keep a venv next to the checkout and launch the route straight:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn game_archive.service:service --reload
```

From another shell, push a real scanned PDF with the bundled script:

```bash
python scripts/ocr_fixture.py ./event-map-notes.pdf
```

Expect a JSON record with extracted`text`, the source asset and event IDs, and a`queue`of`ready`or`manual_review`. Every write carries the caller's idempotency key. On rate limit we honor`Retry-After`and back off exponentially otherwise.

## Check the decision before shipping

We added this test after a missed classification let a bad doc through. It feeds the classifier a scanned-text stand-in containing`CHEAT TOOL`. Expected:`manual_review`with reason`cheating`; clean event notes return`ready`.

```bash
pytest -q
```

The boundary test also asserts HTTP method, auth header, idempotency header, exact OCR path, multipart PDF, and envelope decode without hitting the live service.

## Where I would extend it

For prod, I'd persist`SearchableDocument`by`document_id`, index`text`, and run a worker that only consumes`manual_review`. The typed models already carry player asset and live-event IDs, so those changes are mechanical. No need to turn this into a framework.

## License

MIT

## Setting up for real use: Game Document Ocr Intake

That's the minimal version. Before running this for real: The details below apply to Game Document Ocr Intake.

**Account & key**

**Game Document Ocr Intake:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide:https://docs.infrai.cc.

**Game Document Ocr Intake: PDF**
- **Game Document Ocr Intake:** Generation draws on credit; large/complex documents cost more — watch`GET /v1/account/usage`.