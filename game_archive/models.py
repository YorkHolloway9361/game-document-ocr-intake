from enum import Enum

from pydantic import BaseModel, Field


class AssetKind(str, Enum):
    MAP = "map"
    MOD = "mod"
    SKIN = "skin"


class PlayerAsset(BaseModel):
    asset_id: str
    player_id: str
    kind: AssetKind


class LiveEvent(BaseModel):
    event_id: str
    title: str
    starts_at: str


class DocumentIntakeRequest(BaseModel):
    pdf_base64: str = Field(description="Base64-encoded scanned PDF")
    asset: PlayerAsset
    live_event: LiveEvent | None = None
    lang: str = "eng"
    quality: str = "high"
    idempotency_key: str = Field(min_length=8)


class QueueState(str, Enum):
    READY = "ready"
    MANUAL_REVIEW = "manual_review"


class SearchableDocument(BaseModel):
    document_id: str
    asset: PlayerAsset
    live_event: LiveEvent | None
    text: str
    queue: QueueState
    moderation_reasons: list[str]
