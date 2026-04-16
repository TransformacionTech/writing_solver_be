# Curación automática de contenidos

Módulo que cada 15 días monitorea fuentes web, detecta novedades, genera 3 posts
y los envía por correo. Es independiente del pipeline manual de `/pipeline/run`
pero reutiliza `writer`, `editor` y `reader`.

---

## Flujo

```
Scheduler (15 días)        Tavily → curatorAgent → [Writer → Editor ↔ Reader] × 3
       │                                                                   │
       ▼                                                                   ▼
 run_curation()                                                    send_curation_report
       │                                                                   │
       └─► Supabase (sources, processed_topics, curation_runs)  ◄──────────┘
```

**NO usa `researcher`**: en este flujo la fuente de contenido es Tavily y la
síntesis la hace el `curatorAgent`. El writer recibe el contexto ya resuelto.

---

## Fases

### Fase 1 — Extracción y filtrado
1. `supabase_service.get_active_sources()` → lista de sitios a monitorear
2. `tavily_service.search_source_news(url, days=15)` por cada fuente
3. `supabase_service.is_topic_processed(hash)` para descartar duplicados

### Fase 2 — Procesamiento
1. `curatorAgent` (crew) sintetiza los artículos en 3 temas
2. Por cada tema: `writer` genera borrador → loop `editor ↔ reader` hasta score ≥ 8

### Fase 3 — Notificación
1. `supabase_service.get_active_subscribers()` → lista de emails
2. `sendgrid_service.send_curation_report(subscribers, report)` envía HTML
3. Si no hay novedades: `send_no_news_email()` con aviso breve

### Fase 4 — Registro
1. `supabase_service.save_processed_topic()` por cada tema generado
2. `supabase_service.update_curation_run(status="completed")`

---

## Arquitectura de archivos

```
app/
├── agents/curatorAgent.py           # Agente curador (reemplaza researcher aquí)
├── tasks/curatorTask.py             # Tarea con prompt estructurado
├── services/
│   ├── curation_service.py          # Orquestador (run_curation, run_curation_stream)
│   ├── supabase_service.py          # Cliente + CRUD de tablas
│   ├── tavily_service.py            # Búsqueda web con filtro temporal
│   └── sendgrid_service.py          # HTML + envío de informes
├── routers/curation.py              # Endpoints REST
├── schemas/curation.py              # Pydantic models
└── scheduler.py                     # APScheduler (trigger 15 días)
```

---

## Endpoints

| Método | Path | Descripción |
|---|---|---|
| `POST` | `/curation/run` | Dispara el flujo y devuelve resumen (síncrono) |
| `POST` | `/curation/run-stream` | Dispara el flujo con SSE de progreso paso a paso |
| `GET` | `/curation/runs?limit=N` | Historial de ejecuciones (auditoría) |
| `GET` | `/curation/sources` | Fuentes activas |
| `POST` | `/curation/sources` | Agregar fuente `{name, url}` |
| `GET` | `/curation/subscribers` | Suscriptores activos |
| `POST` | `/curation/subscribers` | Agregar suscriptor `{email}` |

---

## SSE eventos (`/curation/run-stream`)

```json
{"type": "progress", "step": "sources|tavily|dedup|curator|writer|email|register", "message": "..."}
{"type": "result",   "message": "Curación completada: 3 tema(s), correo enviado."}
{"type": "error",    "message": "..."}
{"type": "done"}
```

---

## Supabase — esquema

### `sources`
| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | default `gen_random_uuid()` |
| `name` | text NOT NULL | |
| `url` | text NOT NULL | |
| `active` | bool NOT NULL | default `true` |
| `created_at` | timestamptz | default `now()` |

### `subscribers`
| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `email` | text NOT NULL UNIQUE | |
| `active` | bool NOT NULL | default `true` |

### `curation_runs` — auditoría
| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `run_at` | timestamptz | default `now()` |
| `status` | text | `running` \| `completed` \| `no_news` \| `error` |
| `topics_found` | int | default `0` |
| `email_sent` | bool | default `false` |
| `error_message` | text | nullable |

### `processed_topics` — anti-duplicados
| Columna | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `topic_hash` | text UNIQUE | SHA-256 del título normalizado |
| `topic_text` | text | |
| `sources_used` | jsonb | |
| `posts_generated` | jsonb | |
| `curation_run_id` | uuid FK → `curation_runs.id` | |

**RLS**: todas las tablas tienen RLS habilitado con políticas `anon SELECT/INSERT/UPDATE` según la tabla (ver `curation_service.py` y el SQL de setup).

---

## Scheduler

`app/scheduler.py` — `AsyncIOScheduler` con `IntervalTrigger(days=15)` que
invoca `run_curation()`. Se arranca en el `lifespan` de FastAPI y se detiene
en el shutdown.

**⚠️ Limitación en Render free tier**: el servicio duerme tras 15 min de
inactividad y APScheduler no dispara offline. Para producción estable se
recomienda un cron externo (GitHub Actions, cron-job.org) que llame a
`POST /curation/run` cada 15 días.

---

## Reglas de oro específicas

1. **El curador NO usa RAG** (igual que researcher) — evita contaminar la síntesis con posts previos.
2. **El writer sí usa RAG** para tono (regla general del sistema).
3. **Dedup por hash normalizado**: `sha256(lower().strip())` del título del tema. Si cambia la estrategia de normalización, migrar hashes existentes.
4. **Envío de correos siempre atómico**: si SendGrid falla se registra `email_sent=false` en `curation_runs` pero los posts ya generados se guardan de todos modos.
5. **Streaming vía `sse-starlette`**: `run_curation_stream()` es un `AsyncGenerator[str, None]`; jamás meter `sleep` grande bloqueante.

---

## Variables de entorno requeridas

```env
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_KEY=sb_publishable_...
TAVILY_API_KEY=tvly-...
SENDGRID_API_KEY=SG....
SENDGRID_FROM_EMAIL=<sender verificado en SendGrid>
```

**SendGrid**: el `SENDGRID_FROM_EMAIL` debe estar verificado como Single
Sender o vía Domain Authentication. Sin esto, SendGrid responde 403.
