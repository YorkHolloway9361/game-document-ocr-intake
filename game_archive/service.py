import base64
import binascii

from fastapi import FastAPI, HTTPException

from game_archive.document_intake import ingest_scan
from game_archive.infrai_ocr import InfraiError, InfraiOcrClient
from game_archive.models import DocumentIntakeRequest, SearchableDocument


service = FastAPI(title="Game document OCR intake")


@service.post("/documents/ocr", response_model=SearchableDocument)
def ocr_document(request: DocumentIntakeRequest) -> SearchableDocument:
    try:
        pdf = base64.b64decode(request.pdf_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="pdf_base64 is invalid") from exc
    if not pdf.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Decoded content must be a PDF")

    try:
        return ingest_scan(request, pdf, InfraiOcrClient())
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
