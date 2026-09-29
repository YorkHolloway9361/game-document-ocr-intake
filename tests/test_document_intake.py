from game_archive.document_intake import choose_moderation_queue
from game_archive.models import QueueState


def test_flags_scanned_cheat_listing_for_manual_review() -> None:
    text = "Community map notes: meet at the docks. CHEAT   TOOL download is in the footer."

    queue, reasons = choose_moderation_queue(text)

    assert queue is QueueState.MANUAL_REVIEW
    assert reasons == ["cheating"]


def test_clean_event_notes_are_searchable_without_review() -> None:
    queue, reasons = choose_moderation_queue("Autumn Cup map rotation and spawn notes")

    assert queue is QueueState.READY
    assert reasons == []
