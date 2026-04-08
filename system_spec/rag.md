# Spec: RAG — POST /pipeline/upload-rag

## Endpoint

| Metodo | Path | Content-Type | Respuesta |
|---|---|---|---|
| POST | `/pipeline/upload-rag` | `multipart/form-data` | `RagUploadResponse` JSON |

## Request (FormData)

| Campo | Tipo | Requerido | Default |
|---|---|---|---|
| `file` | UploadFile (.pdf, .txt, .docx) | si | — |
| `source` | string | no | `"manual_upload"` |
| `topic` | string | no | `""` |

## Response schema

```python
class RagUploadResponse(BaseModel):
    status: str           # "ok"
    filename: str
    chunks_stored: int
    document_ids: list[str]
```

## Procesamiento

1. Validar extension (.pdf, .txt, .docx)
2. Extraer texto:
   - PDF: `pypdf.PdfReader`
   - DOCX: `python-docx` (paragraphs)
   - TXT: decode UTF-8
3. Chunkear: 800 caracteres con overlap de 100
4. Indexar cada chunk en ChromaDB con metadata:
   - `source`: nombre del archivo
   - `upload_source`: campo `source` del form ("approved_post", "manual_upload")
   - `topic`: campo `topic` del form (si se envio)
   - `chunk_index`: posicion del chunk

## Proposito del RAG

El RAG es SOLO para tono y formato. Los agentes editoriales (Writer, Editor)
consultan la herramienta `rag_tool` para aprender estilo de posts anteriores
de Tech And Solve. NUNCA se asigna al Researcher (evitar contaminacion factica).

## Seed de referencia

`python -m app.scripts.seed_rag` carga 3 posts de referencia:
- `que_es` — ejemplo de "Que es X"
- `tendencias` — ejemplo de "Tendencias de X"
- `oportunidades_retos` — ejemplo de "Oportunidades y retos de X"

## Archivos involucrados

- `app/routers/rag.py` — endpoint POST /upload-rag
- `app/services/rag_service.py` — add_file(), extract_text(), chunk_text(), query()
- `app/knowledge/rag_tool.py` — RagSearchTool (CrewAI BaseTool)
- `app/schemas/rag.py` — RagUploadResponse
- `app/scripts/seed_rag.py` — seed de posts de referencia
