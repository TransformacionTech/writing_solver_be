import asyncio
import json
import re
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

from crewai import Crew

from app.agents.researcherAgent import researcher
from app.agents.writerAgent import writer
from app.agents.editorAgent import editor
from app.agents.readerAgent import reader
from app.agents.chatAgent import assistant
from app.agents.topicSuggesterAgent import topicSuggester

from app.tasks.researcherTask import researchTask
from app.tasks.writerTask import writerTask
from app.tasks.editorTask import editCopyTask
from app.tasks.readerTask import readerTask
from app.tasks.topicSuggesterTask import topicSuggesterTask

from app.validators.postValidator import validate_post

_executor = ThreadPoolExecutor(max_workers=4)

MAX_EDIT_ITERATIONS = 5


def _run_crew_sync(crew: Crew, inputs: dict) -> str:
    result = crew.kickoff(inputs=inputs)
    return str(result)


async def _run_crew_async(crew: Crew, inputs: dict) -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _run_crew_sync, crew, inputs)


def _parse_score(reader_output: str) -> int:
    """Extract numeric score from reader output like 'Calificación: 8/10'."""
    match = re.search(r"Calificaci[oó]n:\s*(\d+)\s*/\s*10", reader_output)
    return int(match.group(1)) if match else 0


def _extract_post(editor_output: str) -> str:
    """Return the edited post text from editor output."""
    return editor_output.strip()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def run_pipeline(topic: str, context: str | None = None) -> AsyncGenerator[str, None]:
    """
    Phase 1: Researcher → Writer  (sequential crew)
    Phase 2: Editor ↔ Reader loop until score >= 8 or max iterations
    """

    # --- Phase 1: Research & Write ------------------------------------------------
    yield _sse_event("progress", agent="researcher", message="Investigando el tema...")

    phase1_crew = Crew(
        agents=[researcher, writer],
        tasks=[researchTask, writerTask],
        verbose=False,
    )

    draft = await _run_crew_async(phase1_crew, {"topic": topic, "context": context or ""})

    yield _sse_event("progress", agent="researcher", message="Investigación completa.")
    yield _sse_event("progress", agent="writer", message="Borrador escrito.")

    # --- Phase 2: Edit & Validate loop --------------------------------------------
    # Crew instantiated ONCE outside the loop (regla de oro #2)
    phase2_crew = Crew(
        agents=[editor, reader],
        tasks=[editCopyTask, readerTask],
        verbose=False,
    )

    current_post = draft
    score = 0

    for iteration in range(1, MAX_EDIT_ITERATIONS + 1):
        yield _sse_event("progress", agent="editor", message=f"Iteración de edición {iteration}...")

        result = await _run_crew_async(
            phase2_crew,
            {"post": current_post, "feedback": ""},
        )

        # The last task output is the reader evaluation
        score = _parse_score(result)
        # The editor output is the edited post (first task)
        if phase2_crew.tasks_output and len(phase2_crew.tasks_output) >= 2:
            current_post = _extract_post(str(phase2_crew.tasks_output[0]))

        validation = validate_post(score=score)

        if validation.is_valid:
            yield _sse_event("progress", agent="editor", message=f"Post validado con score {score}.")
            break

        yield _sse_event(
            "progress",
            agent="editor",
            message=f"Score {score} < 8, iterando...",
        )

    yield _sse_event("result", post=current_post, score=score)
    yield _sse_event("done")


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

async def chat(message: str, history: list[dict]) -> str:
    from crewai import Task

    chat_task = Task(
        description=f"Responde al usuario: {message}",
        agent=assistant,
        expected_output="Respuesta directa y útil al usuario.",
    )
    chat_crew = Crew(agents=[assistant], tasks=[chat_task], verbose=False)
    result = await _run_crew_async(chat_crew, {})
    return str(result)


# ---------------------------------------------------------------------------
# Topic suggestions
# ---------------------------------------------------------------------------

async def suggest_topics() -> str:
    topics_crew = Crew(
        agents=[topicSuggester],
        tasks=[topicSuggesterTask],
        verbose=False,
    )
    result = await _run_crew_async(topics_crew, {})
    return str(result)


# ---------------------------------------------------------------------------
# SSE helper
# ---------------------------------------------------------------------------

def _sse_event(event_type: str, **kwargs: object) -> str:
    data = {"type": event_type, **kwargs}
    return json.dumps(data, ensure_ascii=False)
