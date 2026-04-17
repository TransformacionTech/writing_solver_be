# Spec: Pipeline — POST /pipeline/run

## Endpoint

| Metodo | Path | Body | Respuesta |
|---|---|---|---|
| POST | `/pipeline/run` | `PipelineRunRequest` | SSE `text/event-stream` |

## Request schema

```python
class PipelineRunRequest(BaseModel):
    topic: str
    context: str | None = None
    user_id: str | None = None
```

## Formato SSE

Cada evento `data:` contiene un JSON con uno de estos tipos:

```
data: {"type": "progress", "agent": "researcher", "message": "..."}
data: {"type": "progress", "agent": "writer", "message": "..."}
data: {"type": "progress", "agent": "editor", "message": "..."}
data: {"type": "result", "post": "...", "score": 9}
data: {"type": "error", "message": "..."}
data: {"type": "done"}
```

- `progress` — emitido por cada agente mientras trabaja
- `result` — solo si el post fue aprobado (score >= 8)
- `error` — si despues de 3 intentos no se alcanzo score 8
- `done` — siempre es el ultimo evento

## Flujo de ejecucion

```
Fase 1: Researcher -> Writer (Crew secuencial)
  - crew.kickoff({"topic": ..., "context": ...})
  - Output: borrador del post

Fase 2: Editor <-> Reader loop (max 3 iteraciones)
  - Crew instanciada UNA VEZ fuera del loop (regla de oro #2)
  - crew.kickoff({"post": ..., "feedback": ...})
  - Reader califica con score X/10
  - Si score >= 8: emitir result + done
  - Si score < 8: pasar feedback del reader al siguiente intento
  - Si 3 intentos fallidos: emitir error + done (NO enviar el post)
```

## Ejecucion asincrona

CrewAI bloquea el hilo. Se ejecuta via `ThreadPoolExecutor`:

```python
_executor = ThreadPoolExecutor(max_workers=4)

async def _run_crew_async(crew, inputs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, crew.kickoff, inputs)
```

## Cancelacion

El frontend puede abortar la request SSE (AbortController). El backend captura
`asyncio.CancelledError` en el generator y detiene la ejecucion limpiamente.

## Archivos involucrados

- `app/routers/pipeline.py` — endpoint POST /run
- `app/services/pipeline_service.py` — run_pipeline(), _run_crew_async()
- `app/validators/postValidator.py` — validate_post(score) -> is_valid
- `app/schemas/pipeline.py` — PipelineRunRequest, eventos SSE
