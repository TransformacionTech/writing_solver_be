from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.core.security import get_current_user
from app.schemas.rag import RagUpdateRequest, RagUpdateResponse, RagUploadResponse
from app.services import rag_service

router = APIRouter(prefix="/pipeline", tags=["rag"])


@router.post("/update-rag", response_model=RagUpdateResponse)
async def update_rag(
    body: RagUpdateRequest,
    _user: dict = Depends(get_current_user),
) -> RagUpdateResponse:
    doc_id = rag_service.add_document(content=body.content, metadata=body.metadata)
    return RagUpdateResponse(status="ok", document_id=doc_id)


@router.post("/upload-rag", response_model=RagUploadResponse)
async def upload_rag_file(
    file: UploadFile,
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
    doc_ids = rag_service.add_file(file_bytes=file_bytes, filename=filename)

    return RagUploadResponse(
        status="ok",
        filename=filename,
        chunks_stored=len(doc_ids),
        document_ids=doc_ids,
    )
