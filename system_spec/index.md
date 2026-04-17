# System Specs — Writing Solver Backend

Carga SOLO la spec relevante a la tarea actual. No cargar todas.

| Spec | Archivo | Cubrimiento |
|---|---|---|
| Pipeline | [pipeline.md](pipeline.md) | `/pipeline/run`, SSE, fases 1 y 2, validacion, loop editor/reader |
| Chat | [chat.md](chat.md) | `/pipeline/chat`, modificacion de post, historial conversacional |
| RAG | [rag.md](rag.md) | `/pipeline/upload-rag`, ChromaDB, chunking, extraccion de texto, seed |
| Topics | [topics.md](topics.md) | `/pipeline/suggest-topics`, agente topicSuggester, parsing de respuesta |
| Auth | [auth.md](auth.md) | GitHub OAuth, JWT, callback flow, security.py |
| Agentes | [agents.md](agents.md) | Researcher, Writer, Editor, Reader, Chat, TopicSuggester — roles, tools, LLM |
| Config | [config.md](config.md) | Variables de entorno, CORS, Pydantic Settings, lifespan |
