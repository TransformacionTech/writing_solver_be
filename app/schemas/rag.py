from pydantic import BaseModel


class RagUploadResponse(BaseModel):
    status: str
    filename: str
    chunks_stored: int
    document_ids: list[str]
