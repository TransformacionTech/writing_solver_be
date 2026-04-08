# Spec: Configuracion y entorno

## Variables de entorno (.env)

```
OPENAI_API_KEY=sk-...           # Obligatorio — LLMs de los agentes
GITHUB_CLIENT_ID=...            # GitHub OAuth App
GITHUB_CLIENT_SECRET=...        # GitHub OAuth App
JWT_SECRET=...                  # Si vacio, usa OPENAI_API_KEY como fallback
JWT_ALGORITHM=HS256
CHROMA_PERSIST_PATH=./chroma_db
CORS_ORIGINS=http://localhost:4200
ENVIRONMENT=development
```

Cargadas con Pydantic Settings en `app/core/config.py`.

## CORS

```python
CORSMiddleware(
    allow_origins=settings.cors_origin_list,  # split por coma
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "Authorization"],
)
```

Frontend Angular en `http://localhost:4200` (dev).

## Lifespan

Al iniciar la app:
- Se crea el directorio `chroma_db/` si no existe

Al cerrar:
- Se hace shutdown del `ThreadPoolExecutor`

## Dependencias principales (requirements.txt)

| Paquete | Uso |
|---|---|
| fastapi | Framework API |
| uvicorn | Servidor ASGI |
| sse-starlette | EventSourceResponse para SSE |
| crewai | Orquestacion de agentes |
| chromadb | Vector store para RAG |
| openai | SDK para LLMs y web search |
| pydantic / pydantic-settings | Validacion y config |
| httpx | Cliente HTTP (GitHub OAuth) |
| python-jose | JWT encode/decode |
| pypdf | Extraccion texto PDF |
| python-docx | Extraccion texto DOCX |
| python-multipart | Upload de archivos |
| pytest / pytest-asyncio | Testing |

## Ejecucion

```bash
# Desarrollo
uvicorn app.main:app --reload --port 8000

# Seed del RAG
python -m app.scripts.seed_rag

# Tests
python -m pytest app/tests/ -x
```

## Archivos involucrados

- `app/core/config.py` — Settings class
- `app/core/security.py` — JWT helpers
- `app/main.py` — FastAPI app, CORS, lifespan, routers
- `.env` / `.env.example` — variables de entorno
- `requirements.txt` — dependencias
