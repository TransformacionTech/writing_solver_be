from pydantic import BaseModel


class RagUpdateRequest(BaseModel):
    content: str
    metadata: dict = {}


class RagUpdateResponse(BaseModel):
    status: str
    document_id: str


class RagUploadResponse(BaseModel):
    status: str
    filename: str
    chunks_stored: int
    document_ids: list[str]
