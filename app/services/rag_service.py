import io
import uuid

import chromadb
from docx import Document as DocxDocument
from pypdf import PdfReader

from app.core.config import settings

_client: chromadb.ClientAPI | None = None
_COLLECTION_NAME = "writing_solver"
_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 100

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.chroma_persist_path)
    return _client


def _get_collection() -> chromadb.Collection:
    return _get_client().get_or_create_collection(name=_COLLECTION_NAME)


# --- Text extraction -----------------------------------------------------------

def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = DocxDocument(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = _get_extension(filename)
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    if ext == ".docx":
        return extract_text_from_docx(file_bytes)
    # .txt
    return file_bytes.decode("utf-8", errors="replace")


def _get_extension(filename: str) -> str:
    return ("." + filename.rsplit(".", 1)[-1]).lower() if "." in filename else ""


# --- Chunking ------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c.strip() for c in chunks if c.strip()]


# --- CRUD ----------------------------------------------------------------------

def add_document(content: str, metadata: dict | None = None) -> str:
    collection = _get_collection()
    doc_id = str(uuid.uuid4())
    collection.add(
        ids=[doc_id],
        documents=[content],
        metadatas=[metadata or {}],
    )
    return doc_id


def add_file(
    file_bytes: bytes,
    filename: str,
    extra_metadata: dict | None = None,
) -> list[str]:
    """Extract text, chunk it, and store each chunk in ChromaDB. Returns chunk IDs."""
    text = extract_text(file_bytes, filename)
    chunks = chunk_text(text)
    collection = _get_collection()
    base_meta = {"source": filename}
    if extra_metadata:
        base_meta.update(extra_metadata)
    ids: list[str] = []
    for i, chunk in enumerate(chunks):
        doc_id = str(uuid.uuid4())
        collection.add(
            ids=[doc_id],
            documents=[chunk],
            metadatas=[{**base_meta, "chunk_index": i}],
        )
        ids.append(doc_id)
    return ids


def query(text: str, n_results: int = 3) -> list[str]:
    collection = _get_collection()
    results = collection.query(query_texts=[text], n_results=n_results)
    return results["documents"][0] if results["documents"] else []
