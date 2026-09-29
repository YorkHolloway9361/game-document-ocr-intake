import hashlib

from game_archive.infrai_ocr import InfraiOcrClient
from game_archive.models import DocumentIntakeRequest, QueueState, SearchableDocument


REVIEW_TERMS = {
    "account theft": "account_safety",
    "cheat tool": "cheating",
    "harassment": "player_safety",
    "real-money trade": "commerce_policy",
}


def choose_moderation_queue(text: str) -> tuple[QueueState, list[str]]:
    normalized = " ".join(text.casefold().split())
    reasons = sorted({reason for term, reason in REVIEW_TERMS.items() if term in normalized})
    state = QueueState.MANUAL_REVIEW if reasons else QueueState.READY
    return state, reasons


def ingest_scan(
    request: DocumentIntakeRequest,
    pdf: bytes,
    client: InfraiOcrClient,
) -> SearchableDocument:
    text = client.ocr_pdf(
        pdf,
        lang=request.lang,
        quality=request.quality,
        idempotency_key=request.idempotency_key,
    )
    queue, reasons = choose_moderation_queue(text)
    digest = hashlib.sha256(pdf).hexdigest()[:16]
    return SearchableDocument(
        document_id=f"doc_{digest}",
        asset=request.asset,
        live_event=request.live_event,
        text=text,
        queue=queue,
        moderation_reasons=reasons,
    )
