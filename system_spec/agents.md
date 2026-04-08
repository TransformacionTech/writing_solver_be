# Spec: Agentes CrewAI

## Arquitectura de agentes

Cada agente tiene un LLM asignado via `app/customLlm/llm.py` usando `crewai.LLM`.

| Agente | Archivo | LLM | Tools | Fase |
|---|---|---|---|---|
| Researcher | `researcherAgent.py` | `llm_researcher` (gpt-4o-mini) | `web_search` | Fase 1 |
| Writer | `writerAgent.py` | `llm_writer` (gpt-5.2) | `rag_tool` | Fase 1 |
| Editor | `editorAgent.py` | `llm_editor` (gpt-5.2) | `rag_tool` | Fase 2 |
| Reader | `readerAgent.py` | `llm_reader` (gpt-4o-mini) | ninguna | Fase 2 |
| Chat Assistant | `chatAgent.py` | `llm_default` (gpt-4o-mini) | ninguna | Chat |
| Topic Suggester | `topicSuggesterAgent.py` | `llm_default` (gpt-4o-mini) | `rag_tool`, `web_search` | Topics |

## Tools

- `rag_tool` (`app/knowledge/rag_tool.py`): consulta ChromaDB para tono y formato
- `web_search` (`app/knowledge/openai_web_search_tool.py`): busqueda web via OpenAI Responses API

## Reglas criticas

1. **RAG NUNCA va al Researcher** — evita contaminacion factica
2. **Writer debe definir el concepto central** antes de cualquier analisis
3. **Writer NO dirige cierres a cargos directivos** a menos que la solicitud lo pida
4. **Reader penaliza** (-1) concepto no definido y (-1) cierre dirigido a cargo especifico

## Reader — Criterios de evaluacion

| Criterio | Peso | Descripcion |
|---|---|---|
| [A] Apertura | /2 | Hook que detiene scroll |
| [B] Voz de marca | /2 | Tono Tech And Solve |
| [C] Impacto comercial | /2 | Genera conversacion |
| [D] Reglas duras | /2 | Longitud, emojis, concepto definido, cierre abierto |
| [E] Cierre | /2 | Pregunta abierta, memorable |

Score minimo para aprobar: **8/10** sin violaciones en [D].

## Modelos LLM (app/customLlm/llm.py)

```python
AGENT_MODELS = {
    "researcher": "gpt-4o-mini",
    "writer": "gpt-5.2",
    "editor": "gpt-5.2",
    "reader": "gpt-4o-mini",
    "default": "gpt-4o-mini",
}
```

## Archivos involucrados

- `app/agents/` — definicion de cada agente (role, goal, backstory, tools, llm)
- `app/tasks/` — definicion de cada tarea (description, expected_output, agent)
- `app/customLlm/llm.py` — instancias LLM por rol
- `app/knowledge/` — rag_tool.py, openai_web_search_tool.py
