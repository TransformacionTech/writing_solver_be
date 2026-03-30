# CLAUDE.md — Writing Solver Backend

Memoria persistente del proyecto. Leer antes de cualquier intervención.

---

## 1. Proyecto

API central para orquestación de agentes CrewAI orientados a generación, edición
y validación de posts LinkedIn para Tech And Solve. Expone endpoints REST + SSE
que consume el frontend Angular 21 (Writing Solver Frontend).

---

## 2. Stack

| Capa | Tecnología | Versión mínima |
|---|---|---|
| Framework API | FastAPI | 0.115+ |
| Servidor ASGI | Uvicorn | 0.30+ |
| SSE | sse-starlette | 2.1+ |
| Orquestación agentes | CrewAI | 0.80.0+ |
| Vectores / RAG | ChromaDB | 0.5+ |
| LLMs | OpenAI SDK | 1.x |
| Validación | Pydantic v2 | 2.7+ |
| Ejecución async | asyncio + ThreadPoolExecutor (stdlib) | — |
| HTTP cliente | httpx | 0.27+ |
| Config | Pydantic Settings + python-dotenv | — |
| Tests | pytest + pytest-asyncio + httpx[testing] | — |
| Linting | ruff | — |

---

## 3. Arquitectura

### Patrón
REST + SSE · Multi-Agente Modular · sin estado entre requests.

### Capas
```
app/
├── main.py             # FastAPI app, CORS, lifespan, include_router
├── routers/
│   ├── pipeline.py     # /pipeline/run, /pipeline/chat
│   ├── topics.py       # /pipeline/suggest-topics
│   └── rag.py          # /pipeline/update-rag
├── agents/             # HEREDADO — NO MODIFICAR lógica interna
├── tasks/              # HEREDADO — NO MODIFICAR
├── PROMPTS/            # HEREDADO — NO MODIFICAR
├── validators/
│   └── postValidator.py  # Score >= 8 → éxito
├── customLlm/
│   └── llm.py          # LLM por agente (gpt-4o-mini, gpt-5.x…)
├── services/
│   ├── pipeline_service.py  # Orquesta crew async vía executor
│   ├── rag_service.py       # Consulta ChromaDB
│   └── auth_service.py      # GitHub OAuth code exchange → JWT
├── schemas/            # Pydantic models (request/response)
├── core/
│   ├── config.py       # Pydantic Settings (env vars)
│   └── security.py     # JWT encode/decode
└── tests/
```

### Flujo de datos — POST /pipeline/run
```
Angular POST JSON
  → FastAPI router valida schema (Pydantic)
  → pipeline_service.run() en ThreadPoolExecutor
      → Fase 1: ResearcherAgent → WriterAgent  (crew.kickoff())
      → Fase 2: EditorAgent ↔ ReaderAgent loop (crew.kickoff() recursivo)
      → postValidator verifica Score >= 8
  → SSE emite eventos parciales al cliente
  → Respuesta final JSON con post validado
```

---

## 4. Endpoints (contrato con el frontend)

Todos los endpoints usan prefijo `/pipeline`.

| Método | Path | Body | Respuesta |
|---|---|---|---|
| POST | `/pipeline/run` | `PipelineRunRequest` | SSE `text/event-stream` |
| POST | `/pipeline/chat` | `ChatRequest` | `ChatResponse` JSON |
| GET | `/pipeline/suggest-topics` | query params | `TopicsResponse` JSON |
| POST | `/pipeline/update-rag` | `RagUpdateRequest` | `RagUpdateResponse` JSON |

### Schemas mínimos (Pydantic v2)
```python
class PipelineRunRequest(BaseModel):
    topic: str
    context: str | None = None
    user_id: str

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

class RagUpdateRequest(BaseModel):
    content: str
    metadata: dict = {}
```

### Formato SSE
Cada evento SSE debe tener la estructura que espera el frontend Angular:
```
data: {"type": "progress", "agent": "researcher", "message": "..."}
data: {"type": "progress", "agent": "writer", "message": "..."}
data: {"type": "result", "post": "...", "score": 9}
data: {"type": "done"}
```

---

## 5. CORS

El frontend Angular corre en `http://localhost:4200` en desarrollo.
Configurar `CORSMiddleware` para:
- `allow_origins`: `["http://localhost:4200"]` (dev) + dominio producción (env var)
- `allow_methods`: `["*"]`
- `allow_headers`: `["*", "Authorization"]`

---

## 6. Auth

- GitHub OAuth: el frontend redirige al usuario a GitHub; este backend implementa
  el endpoint que recibe el `code`, lo intercambia por `access_token` con httpx,
  obtiene el perfil del usuario y retorna un JWT firmado.
- JWT: cada request protegido lleva `Authorization: Bearer <token>` — validar con
  `security.py` en un `Depends`.
- El frontend NO implementa OAuth propio; solo almacena y adjunta el JWT.

---

## 7. Ejecución asíncrona de CrewAI

CrewAI bloquea el hilo. Nunca llamar `crew.kickoff()` directamente en un
endpoint async. Usar siempre:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=4)

async def run_crew_async(crew, inputs: dict):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, crew.kickoff, inputs)
```

El executor se crea una sola vez en el lifespan de la app.

---

## 8. Reglas de oro (OBLIGATORIAS)

1. **Módulos heredados intocables**: `agents/`, `tasks/`, `PROMPTS/`.
   No refactorizar lógica interna, nombres, ni prompts. Solo leer e invocar.

2. **Fase 2 — instanciación fuera del loop**:
   La Crew Editor+Reader se instancia UNA VEZ. Dentro del loop de validación
   solo se llama `crew.kickoff()`, nunca `Crew(...)`.

3. **RAG solo para tono y formato**:
   La `rag_tool` (ChromaDB) únicamente se asigna a agentes editoriales.
   NUNCA asignarla al `ResearcherAgent` para evitar contaminación fáctica.

4. **Pydantic v2 estricto**:
   Toda salida de CrewAI se parsea con un modelo Pydantic antes de retornar
   al cliente. Sin `dict` sueltos en las responses.

5. **SSE via sse-starlette**:
   No usar Response manual. Usar `EventSourceResponse` de `sse_starlette`.

---

## 9. Variables de entorno (.env)
```
OPENAI_API_KEY=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
JWT_SECRET=
JWT_ALGORITHM=HS256
CHROMA_PERSIST_PATH=./chroma_db
CORS_ORIGINS=http://localhost:4200
ENVIRONMENT=development
```

Cargar con `Pydantic Settings` en `core/config.py`.

---

## 10. Convenciones

- PEP-8. Nombres en inglés salvo comentarios/commits.
- Type hints en todas las funciones.
- Un router por dominio funcional.
- Tests en `tests/` con prefijo `test_`.
- `pytest-asyncio` para endpoints async con `httpx.AsyncClient`.

---

## 11. Specs detalladas

Ver `system_spec/index.md` — cargar solo el relevante a la tarea actual.