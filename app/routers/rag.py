from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from app.core.security import get_current_user
from app.schemas.rag import RagUploadResponse
from app.services import rag_service

router = APIRouter(prefix="/pipeline", tags=["rag"])


@router.post("/upload-rag", response_model=RagUploadResponse)
async def upload_rag_file(
    file: UploadFile,
    source: str = Form("manual_upload"),
    topic: str = Form(""),
    _user: dict = Depends(get_current_user),
) -> RagUploadResponse:
    filename = file.filename or "unknown"
    ext = ("." + filename.rsplit(".", 1)[-1]).lower() if "." in filename else ""

    if ext not in rag_service.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Allowed: {', '.join(rag_service.ALLOWED_EXTENSIONS)}",
        )

    file_bytes = await file.read()

    extra_metadata: dict[str, str] = {"upload_source": source}
    if topic:
        extra_metadata["topic"] = topic

    doc_ids = rag_service.add_file(
        file_bytes=file_bytes,
        filename=filename,
        extra_metadata=extra_metadata,
    )

    return RagUploadResponse(
        status="ok",
        filename=filename,
        chunks_stored=len(doc_ids),
        document_ids=doc_ids,
    )
