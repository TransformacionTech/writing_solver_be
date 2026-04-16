"""
Curation service — orchestrates the full 15-day content curation pipeline.

Flow:
  1. Fetch active sources from Supabase
  2. Search each source via Tavily (last 15 days)
  3. curatorAgent synthesizes articles → 3 new topics (dedup via Supabase)
  4. For each topic: writer → editor ↔ reader loop (reusing pipeline_service logic)
  5. Send HTML report via SendGrid
  6. Register processed topics in Supabase
  7. Update curation_run audit row
"""
from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from crewai import Crew

from app.agents.curatorAgent import curator
from app.agents.writerAgent import writer
from app.agents.editorAgent import editor
from app.agents.readerAgent import reader

from app.tasks.curatorTask import curatorTask
from app.tasks.writerTask import writerTask
from app.tasks.editorTask import editCopyTask
from app.tasks.readerTask import readerTask

from app.validators.postValidator import validate_post

from app.core.config import settings
from app.services import supabase_service as supa
from app.services import tavily_service as tavily
from app.services import sendgrid_service as sg_service

_executor = ThreadPoolExecutor(max_workers=2)

MAX_EDIT_ITERATIONS = 3


# ---------------------------------------------------------------------------
# Internal helpers (mirror pipeline_service pattern)
# ---------------------------------------------------------------------------

def _run_sync(crew: Crew, inputs: dict) -> object:
    return crew.kickoff(inputs=inputs)


async def _run_async(crew: Crew, inputs: dict) -> object:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _run_sync, crew, inputs)


def _parse_score(text: str) -> int:
    match = re.search(r"Calificaci[oó]n:\s*(\d+)\s*/\s*10", text)
    return int(match.group(1)) if match else 0


# ---------------------------------------------------------------------------
# Step 1 — collect articles from all sources via Tavily
# ---------------------------------------------------------------------------

def _collect_articles(sources: list[dict]) -> list[dict]:
    all_articles: list[dict] = []
    for source in sources:
        articles = tavily.search_source_news(source["url"])
        all_articles.extend(articles)
    return all_articles


# ---------------------------------------------------------------------------
# Step 2 — run curatorAgent to get 3 synthesized topics
# ---------------------------------------------------------------------------

async def _curate_topics(
    articles: list[dict],
    processed_topics: list[str],
) -> str:
    """Run the curator crew and return its raw text output."""
    articles_text = json.dumps(articles, ensure_ascii=False, indent=2)
    processed_text = "\n".join(f"- {t}" for t in processed_topics) or "Ninguno aún."

    crew = Crew(
        agents=[curator],
        tasks=[curatorTask],
        verbose=False,
    )
    result = await _run_async(
        crew,
        {"articles": articles_text, "processed_topics": processed_text},
    )
    return str(result)


# ---------------------------------------------------------------------------
# Step 3 — parse curator output into individual topic blocks
# ---------------------------------------------------------------------------

def _parse_curator_output(raw: str) -> list[dict]:
    """
    Parse the curator output into a list of dicts:
    [{ title, resumen, datos_clave, fuentes, relevancia }]
    """
    topics: list[dict] = []
    blocks = re.split(r"---\s*\n", raw)

    for block in blocks:
        block = block.strip()
        if not block or not block.startswith("TEMA"):
            continue

        def _extract(field: str) -> str:
            pattern = rf"{field}:\s*(.*?)(?=\n[A-ZÁÉÍÓÚ][a-záéíóúñ\s]+:|$)"
            m = re.search(pattern, block, re.DOTALL)
            return m.group(1).strip() if m else ""

        title = _extract("Título")
        if not title:
            continue

        topics.append(
            {
                "title": title,
                "resumen": _extract("Resumen"),
                "datos_clave": _extract("Datos clave"),
                "fuentes": _extract("Fuentes usadas"),
                "relevancia": _extract("Relevancia sectorial"),
            }
        )

    return topics[:3]


# ---------------------------------------------------------------------------
# Step 4 — generate one post per topic using writer → editor ↔ reader
# ---------------------------------------------------------------------------

async def _generate_post(topic: dict) -> tuple[str, int]:
    """
    Run the write+edit+validate loop for a single topic dict.
    Returns (final_post_text, score).
    """
    context = (
        f"RESUMEN:\n{topic['resumen']}\n\n"
        f"DATOS CLAVE:\n{topic['datos_clave']}\n\n"
        f"FUENTES:\n{topic['fuentes']}\n\n"
        f"RELEVANCIA SECTORIAL:\n{topic['relevancia']}"
    )
    topic_input = topic["title"]

    # Phase 1 — Write (no researcher: curator already did the research)
    write_crew = Crew(agents=[writer], tasks=[writerTask], verbose=False)
    write_result = await _run_async(write_crew, {"topic": topic_input, "context": context})
    draft = str(write_result)

    # Phase 2 — Edit ↔ Reader loop
    edit_crew = Crew(agents=[editor, reader], tasks=[editCopyTask, readerTask], verbose=False)
    current_post = draft
    score = 0
    feedback = ""

    for _ in range(MAX_EDIT_ITERATIONS):
        phase2_result = await _run_async(edit_crew, {"post": current_post, "feedback": feedback})
        reader_output = str(phase2_result)
        score = _parse_score(reader_output)
        feedback = reader_output

        if phase2_result.tasks_output and len(phase2_result.tasks_output) >= 2:
            current_post = str(phase2_result.tasks_output[0]).strip()

        if validate_post(score=score).is_valid:
            break

    return current_post, score


# ---------------------------------------------------------------------------
# Step 5 — build the SendGrid report payload
# ---------------------------------------------------------------------------

def _build_report(
    topics: list[dict],
    posts: list[tuple[str, int]],
    articles: list[dict],
    run_date: str,
) -> dict:
    # Unique source names/urls
    seen_urls: set[str] = set()
    sources: list[dict] = []
    for a in articles:
        url = a.get("source", a.get("url", ""))
        if url and url not in seen_urls:
            seen_urls.add(url)
            sources.append({"name": url, "url": url})

    # Summary: first article contents joined
    summary_parts = [a.get("content", "")[:300] for a in articles[:3] if a.get("content")]
    summary = " ".join(summary_parts) or "Se encontraron novedades en las fuentes monitoreadas."

    # Topics by source
    topics_by_source: list[dict] = [
        {"source": t["fuentes"] or "varias fuentes", "topics": [t["title"]]}
        for t in topics
    ]

    # Posts
    report_posts = [
        {
            "title": topics[i]["title"] if i < len(topics) else f"Post {i + 1}",
            "content": post_text,
            "why_relevant": topics[i]["relevancia"] if i < len(topics) else "",
            "source": topics[i]["fuentes"] if i < len(topics) else "",
        }
        for i, (post_text, _score) in enumerate(posts)
    ]

    # Overall title: first topic title
    title = topics[0]["title"] if topics else "Novedades del Sector Asegurador"

    return {
        "title": title,
        "sources": sources,
        "summary": summary,
        "topics_by_source": topics_by_source,
        "posts": report_posts,
        "run_date": run_date,
    }


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

async def run_curation() -> dict:
    """
    Execute the full curation pipeline.
    Returns a summary dict with status, topics_found, email_sent.
    """
    run_date = datetime.now().strftime("%d/%m/%Y")
    run_id = supa.create_curation_run()

    try:
        # 1. Sources
        sources = supa.get_active_sources()
        if not sources:
            supa.update_curation_run(run_id, status="no_news", topics_found=0)
            return {"status": "no_news", "reason": "No active sources configured."}

        # 2. Collect articles via Tavily
        articles = _collect_articles(sources)
        if not articles:
            subscribers = supa.get_active_subscribers()
            email_sent = sg_service.send_no_news_email(subscribers, run_date)
            supa.update_curation_run(
                run_id, status="no_news", topics_found=0, email_sent=email_sent
            )
            return {"status": "no_news", "topics_found": 0, "email_sent": email_sent}

        # 3. Curate topics — dedup against already processed
        # Fetch last ~100 processed topic texts for dedup context
        processed_resp = (
            supa.get_client()
            .table("processed_topics")
            .select("topic_text")
            .order("processed_at", desc=True)
            .limit(100)
            .execute()
        )
        processed_topics = [row["topic_text"] for row in (processed_resp.data or [])]

        curator_raw = await _curate_topics(articles, processed_topics)
        topics = _parse_curator_output(curator_raw)

        if not topics:
            subscribers = supa.get_active_subscribers()
            email_sent = sg_service.send_no_news_email(subscribers, run_date)
            supa.update_curation_run(
                run_id, status="no_news", topics_found=0, email_sent=email_sent
            )
            return {"status": "no_news", "topics_found": 0, "email_sent": email_sent}

        # 4. Generate one post per topic
        posts: list[tuple[str, int]] = []
        for topic in topics:
            post_text, score = await _generate_post(topic)
            posts.append((post_text, score))

        # 5. Build report and send email
        report = _build_report(topics, posts, articles, run_date)
        subscribers = supa.get_active_subscribers()
        email_sent = sg_service.send_curation_report(subscribers, report)

        # 6. Register processed topics
        for i, topic in enumerate(topics):
            post_text, _ = posts[i]
            supa.save_processed_topic(
                topic_text=topic["title"],
                sources_used=[{"url": u} for u in topic["fuentes"].split("\n") if u.strip()],
                posts_generated=[post_text],
                curation_run_id=run_id,
            )

        # 7. Update audit row
        supa.update_curation_run(
            run_id,
            status="completed",
            topics_found=len(topics),
            email_sent=email_sent,
        )

        return {
            "status": "completed",
            "topics_found": len(topics),
            "email_sent": email_sent,
            "run_id": run_id,
        }

    except Exception as exc:
        supa.update_curation_run(
            run_id, status="error", error_message=str(exc)
        )
        raise


# ---------------------------------------------------------------------------
# Streaming variant — emits SSE-friendly events for real-time UI
# ---------------------------------------------------------------------------

def _evt(event_type: str, **kwargs: object) -> str:
    return json.dumps({"type": event_type, **kwargs}, ensure_ascii=False)


async def run_curation_stream() -> AsyncGenerator[str, None]:
    """
    Same flow as `run_curation` but yields JSON events for SSE streaming.
    Events:
      { type: 'progress', step, message }
      { type: 'result', message, detail }
      { type: 'error', message }
      { type: 'done' }
    """
    run_date = datetime.now().strftime("%d/%m/%Y")

    try:
        yield _evt("progress", step="init", message="Creando run en Supabase...")
        run_id = supa.create_curation_run()

        yield _evt("progress", step="sources", message="Consultando fuentes activas...")
        sources = supa.get_active_sources()
        if not sources:
            supa.update_curation_run(run_id, status="no_news", topics_found=0)
            yield _evt("error", message="No hay fuentes activas configuradas.")
            yield _evt("done")
            return
        yield _evt("progress", step="sources", message=f"{len(sources)} fuente(s) encontrada(s).")

        yield _evt("progress", step="tavily", message="Buscando novedades en Tavily (últimos 15 días)...")
        articles = _collect_articles(sources)
        yield _evt("progress", step="tavily", message=f"{len(articles)} artículo(s) recuperado(s).")

        if not articles:
            subscribers = supa.get_active_subscribers()
            yield _evt("progress", step="email", message=f"Sin novedades. Enviando aviso a {len(subscribers)} suscriptor(es)...")
            try:
                email_sent = sg_service.send_no_news_email(subscribers, run_date)
            except Exception as e:
                email_sent = False
                yield _evt("progress", step="email", message=f"No se pudo enviar el correo: {e}")
            supa.update_curation_run(run_id, status="no_news", topics_found=0, email_sent=email_sent)
            yield _evt("result", message="Sin novedades. Correo informativo enviado." if email_sent else "Sin novedades.")
            yield _evt("done")
            return

        yield _evt("progress", step="dedup", message="Cargando historial de temas procesados...")
        processed_resp = (
            supa.get_client()
            .table("processed_topics")
            .select("topic_text")
            .order("processed_at", desc=True)
            .limit(100)
            .execute()
        )
        processed_topics = [row["topic_text"] for row in (processed_resp.data or [])]
        yield _evt("progress", step="dedup", message=f"{len(processed_topics)} tema(s) previos.")

        yield _evt("progress", step="curator", message="Curador sintetizando 3 temas nuevos...")
        curator_raw = await _curate_topics(articles, processed_topics)
        topics = _parse_curator_output(curator_raw)

        if not topics:
            subscribers = supa.get_active_subscribers()
            yield _evt("progress", step="email", message="Curador no encontró temas nuevos. Enviando aviso...")
            try:
                email_sent = sg_service.send_no_news_email(subscribers, run_date)
            except Exception as e:
                email_sent = False
                yield _evt("progress", step="email", message=f"No se pudo enviar el correo: {e}")
            supa.update_curation_run(run_id, status="no_news", topics_found=0, email_sent=email_sent)
            yield _evt("result", message="Sin temas nuevos. Correo informativo enviado." if email_sent else "Sin temas nuevos.")
            yield _evt("done")
            return

        yield _evt("progress", step="curator", message=f"{len(topics)} tema(s) identificado(s).")

        posts: list[tuple[str, int]] = []
        for i, topic in enumerate(topics, 1):
            yield _evt("progress", step="writer", message=f"Generando post {i}/{len(topics)}: {topic['title'][:60]}...")
            post_text, score = await _generate_post(topic)
            posts.append((post_text, score))
            yield _evt("progress", step="writer", message=f"Post {i} listo (score {score}/10).")

        yield _evt("progress", step="email", message="Construyendo informe HTML...")
        report = _build_report(topics, posts, articles, run_date)

        subscribers = supa.get_active_subscribers()
        yield _evt("progress", step="email", message=f"Enviando a {len(subscribers)} suscriptor(es): {subscribers} desde {settings.sendgrid_from_email}...")
        try:
            result = sg_service.send_curation_report(subscribers, report)
            email_sent = bool(result)
            yield _evt("progress", step="email", message=f"SendGrid respondió: {result.detail}")
        except Exception as e:
            email_sent = False
            yield _evt("progress", step="email", message=f"Error SendGrid: {e}")

        yield _evt("progress", step="register", message="Registrando temas procesados...")
        for i, topic in enumerate(topics):
            post_text, _ = posts[i]
            supa.save_processed_topic(
                topic_text=topic["title"],
                sources_used=[{"url": u} for u in topic["fuentes"].split("\n") if u.strip()],
                posts_generated=[post_text],
                curation_run_id=run_id,
            )

        supa.update_curation_run(
            run_id,
            status="completed",
            topics_found=len(topics),
            email_sent=email_sent,
        )

        yield _evt(
            "result",
            message=f"Curación completada: {len(topics)} tema(s), correo {'enviado' if email_sent else 'NO enviado'}.",
        )
        yield _evt("done")

    except Exception as exc:
        yield _evt("error", message=str(exc))
        yield _evt("done")
