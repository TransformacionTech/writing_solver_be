# Spec: Topics — GET /pipeline/suggest-topics

## Endpoint

| Metodo | Path | Auth | Respuesta |
|---|---|---|---|
| GET | `/pipeline/suggest-topics` | Bearer JWT | `TopicsResponse` JSON |

## Response schema

```python
class TopicsResponse(BaseModel):
    topics: list[str]   # lista de 5 temas sugeridos
```

## Ejemplo de respuesta

```json
{
  "topics": [
    "Seguros parametricos: como funcionan y por que crecen en LATAM",
    "Open Insurance: el proximo paso despues del Open Banking",
    "IA en deteccion de fraude: casos reales en aseguradoras",
    "Microseguros digitales para economia informal",
    "Experiencia del asegurado: autoservicio vs atencion humana"
  ]
}
```

## Comportamiento

- Usa el agente `topicSuggester` con `topicSuggesterTask`
- El agente consulta RAG (posts anteriores) + web search (tendencias actuales)
- La salida del agente se parsea con regex para extraer los 5 titulos
- Fallback: si el parsing falla, se divide por bloques de texto

## Archivos involucrados

- `app/routers/topics.py` — endpoint GET /suggest-topics
- `app/services/pipeline_service.py` — suggest_topics()
- `app/agents/topicSuggesterAgent.py` — topicSuggester agent
- `app/tasks/topicSuggesterTask.py` — topicSuggesterTask
- `app/schemas/topics.py` — TopicsResponse
