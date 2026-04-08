# CLAUDE.md — Writing Solver Backend

Leer antes de cualquier intervención. Para detalle, cargar solo la spec
relevante desde `system_spec/index.md`.

---

## Estrategia de ramas — LEER ANTES DE HACER CAMBIOS

| Rama | Propósito | Frontend esperado |
|---|---|---|
| `main` | Desarrollo local | `http://localhost:4200` |
| `deploy` | Producción en Render | `https://writing-solver-fe.onrender.com` |

**Reglas:**
- Desarrollar en `main`. Merge a `deploy` para desplegar a producción.
- El archivo `.env` **nunca se sube** al repo. Render usa variables de entorno del dashboard.

### Archivos que difieren entre ramas

**`main` (local):**
- `app/core/config.py` → `cors_origins: "http://localhost:4200"`, sin `frontend_url`
- `.env` → credenciales de desarrollo (no se sube al repo)

**`deploy` (Render):**
- `app/core/config.py` → `cors_origins: "https://writing-solver-fe.onrender.com"`, `frontend_url: "https://writing-solver-fe.onrender.com"`
- Variables de entorno configuradas en el dashboard de Render (no en `.env`)

### Ejecución local (rama `main`)
```bash
uvicorn app.main:app --reload   # http://localhost:8000
```

---

## Proyecto

API FastAPI para orquestación de agentes CrewAI orientados a generación,
edición y validación de posts LinkedIn para Tech And Solve.
Frontend local: `http://localhost:4200` | Frontend producción: `https://writing-solver-fe.onrender.com`.

---

## Estructura

```
app/
├── main.py                  # FastAPI app, CORS, lifespan
├── routers/                 # pipeline.py, topics.py, rag.py, auth.py
├── services/                # pipeline_service.py, rag_service.py, auth_service.py
├── schemas/                 # Pydantic v2 request/response models
├── agents/                  # CrewAI agents (NO modificar lógica interna)
├── tasks/                   # CrewAI tasks (NO modificar lógica interna)
├── knowledge/               # rag_tool.py, openai_web_search_tool.py
├── validators/              # postValidator.py (score >= 8)
├── customLlm/               # llm.py (LLM por agente)
├── core/                    # config.py, security.py
├── scripts/                 # seed_rag.py
└── tests/
```

---

## Endpoints

| Método | Path | Spec |
|---|---|---|
| POST | `/pipeline/run` | [pipeline.md](system_spec/pipeline.md) |
| POST | `/pipeline/chat` | [chat.md](system_spec/chat.md) |
| GET | `/pipeline/suggest-topics` | [topics.md](system_spec/topics.md) |
| POST | `/pipeline/upload-rag` | [rag.md](system_spec/rag.md) |
| POST | `/auth/github` | [auth.md](system_spec/auth.md) |
| GET | `/auth/callback` | [auth.md](system_spec/auth.md) |

---

## Reglas de oro (OBLIGATORIAS)

1. **Módulos heredados intocables**: `agents/`, `tasks/`.
   No refactorizar lógica interna, nombres, ni prompts. Solo leer e invocar.

2. **Fase 2 — instanciación fuera del loop**:
   La Crew Editor+Reader se instancia UNA VEZ. Dentro del loop solo `crew.kickoff()`.

3. **RAG solo para tono y formato**:
   `rag_tool` solo va a Writer, Editor y TopicSuggester. NUNCA al Researcher.

4. **Pydantic v2 estricto**:
   Toda salida de CrewAI se parsea con modelo Pydantic antes de retornar.

5. **SSE via sse-starlette**:
   Usar `EventSourceResponse`. Eventos: `progress`, `result`, `error`, `done`.

6. **CrewAI nunca en hilo async**:
   Siempre ejecutar via `ThreadPoolExecutor` con `run_in_executor`.

---

## Convenciones

- PEP-8. Nombres en inglés salvo comentarios/commits.
- Type hints en todas las funciones.
- Un router por dominio funcional.
- Tests con prefijo `test_`, ejecutar con `pytest`.

---

## Specs detalladas

Ver [`system_spec/index.md`](system_spec/index.md) — cargar solo la relevante a la tarea.

| Spec | Área |
|---|---|
| [pipeline.md](system_spec/pipeline.md) | SSE, fases, validación, loop |
| [chat.md](system_spec/chat.md) | Chat conversacional, modificación de post |
| [rag.md](system_spec/rag.md) | Upload archivos, ChromaDB, chunking |
| [topics.md](system_spec/topics.md) | Sugerencia de temas |
| [auth.md](system_spec/auth.md) | GitHub OAuth, JWT |
| [agents.md](system_spec/agents.md) | Agentes, tools, LLMs, criterios evaluación |
| [config.md](system_spec/config.md) | Env vars, CORS, dependencias, ejecución |
