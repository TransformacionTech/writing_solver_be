# Spec: Chat — POST /pipeline/chat

## Endpoint

| Metodo | Path | Body | Respuesta |
|---|---|---|---|
| POST | `/pipeline/chat` | `ChatRequest` | `ChatResponse` JSON |

## Request schema

```python
class ChatMessage(BaseModel):
    role: str          # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    mensaje: str       # instruccion o pregunta del usuario
    post_actual: str   # el post generado como contexto
    history: list[ChatMessage] = []
```

## Response schema

```python
class ChatResponse(BaseModel):
    respuesta: str       # post modificado o respuesta textual
    post_modificado: bool  # true si el post fue modificado
```

## Comportamiento

1. **Modificacion** (`post_modificado: true`):
   Si el usuario pide un cambio (ej: "usa negritas", "hazlo mas corto"),
   `respuesta` contiene el post COMPLETO con las modificaciones aplicadas.
   No explicaciones, no un post nuevo — el MISMO post editado.

2. **Pregunta** (`post_modificado: false`):
   Si el usuario hace una pregunta (ej: "cuantas palabras tiene?"),
   `respuesta` contiene texto libre respondiendo la pregunta.

## Deteccion de intencion

Heuristica por keywords: si el mensaje contiene palabras como
"cambia", "modifica", "agrega", "quita", "hazlo", "negritas", "acorta",
etc., se trata como modificacion.

## Agente

Usa el `assistant` de `app/agents/chatAgent.py` con `llm_default`.
Se crea un `Task` dinamico por cada request con el post_actual como contexto
y el historial de conversacion.

## Archivos involucrados

- `app/routers/pipeline.py` — endpoint POST /chat
- `app/services/pipeline_service.py` — chat()
- `app/agents/chatAgent.py` — assistant agent
- `app/schemas/chat.py` — ChatRequest, ChatResponse
