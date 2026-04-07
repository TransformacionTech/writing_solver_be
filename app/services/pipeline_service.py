import asyncio
import json
import re
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor

from crewai import Crew, Task
from crewai.crew import CrewOutput

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

MAX_EDIT_ITERATIONS = 3


def _run_crew_sync(crew: Crew, inputs: dict) -> CrewOutput:
    return crew.kickoff(inputs=inputs)


async def _run_crew_async(crew: Crew, inputs: dict) -> CrewOutput:
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
    Phase 1: Researcher -> Writer  (sequential crew)
    Phase 2: Editor <-> Reader loop until score >= 8 or max iterations
    """

    # --- Phase 1: Research & Write ------------------------------------------------
    yield _sse_event("progress", agent="researcher", message="Investigando el tema...")

    phase1_crew = Crew(
        agents=[researcher, writer],
        tasks=[researchTask, writerTask],
        verbose=False,
    )

    phase1_result = await _run_crew_async(phase1_crew, {"topic": topic, "context": context or ""})
    draft = str(phase1_result)

    yield _sse_event("progress", agent="researcher", message="Investigacion completa.")
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
    feedback = ""
    approved = False

    for iteration in range(1, MAX_EDIT_ITERATIONS + 1):
        yield _sse_event("progress", agent="editor", message=f"Iteracion de edicion {iteration} de {MAX_EDIT_ITERATIONS}...")

        phase2_result = await _run_crew_async(
            phase2_crew,
            {"post": current_post, "feedback": feedback},
        )

        # Extract outputs from CrewOutput
        reader_output = str(phase2_result)
        score = _parse_score(reader_output)
        feedback = reader_output

        # The editor output is the first task's result
        if phase2_result.tasks_output and len(phase2_result.tasks_output) >= 2:
            current_post = _extract_post(str(phase2_result.tasks_output[0]))

        validation = validate_post(score=score)

        if validation.is_valid:
            yield _sse_event("progress", agent="editor", message=f"Post aprobado con score {score}/10.")
            approved = True
            break

        yield _sse_event(
            "progress",
            agent="editor",
            message=f"Score {score}/10 - no alcanza el minimo de 8. Reintentando ({iteration}/{MAX_EDIT_ITERATIONS})...",
        )

    if approved:
        yield _sse_event("result", post=current_post, score=score)
    else:
        yield _sse_event(
            "error",
            message=f"El post no alcanzo la calificacion minima de 8/10 despues de {MAX_EDIT_ITERATIONS} intentos. Ultimo score: {score}/10. Intenta con un topic diferente o mas contexto.",
        )
    yield _sse_event("done")


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

_MODIFICATION_KEYWORDS = [
    "cambia", "modifica", "agrega", "quita", "elimina", "acorta",
    "alarga", "reescribe", "usa", "pon", "hazlo", "ajusta",
    "reemplaza", "incluye", "negritas", "bold", "corto", "largo",
    "hashtag", "emoji", "estadistica", "dato", "cierre", "gancho",
    "titulo", "edita", "mejora", "reformula", "simplifica",
]


def _is_modification_request(mensaje: str) -> bool:
    """Heuristic: does the user want to modify the post?"""
    msg_lower = mensaje.lower()
    return any(kw in msg_lower for kw in _MODIFICATION_KEYWORDS)


async def chat(
    mensaje: str,
    post_actual: str,
    history: list[dict],
) -> dict:
    """
    Chat endpoint that receives the current post as context.
    Returns { respuesta: str, post_modificado: bool }
    """
    is_modification = _is_modification_request(mensaje)

    if is_modification:
        description = (
            f"El usuario quiere modificar el siguiente post de LinkedIn.\n\n"
            f"POST ACTUAL:\n{post_actual}\n\n"
            f"INSTRUCCION DEL USUARIO: {mensaje}\n\n"
            f"Aplica EXACTAMENTE lo que pide el usuario al post. "
            f"Devuelve UNICAMENTE el post completo modificado, sin explicaciones, "
            f"sin preambulos, sin comentarios adicionales. Solo el post."
        )
        expected = "El post completo modificado segun la instruccion del usuario. SOLO el post, nada mas."
    else:
        description = (
            f"El usuario tiene una pregunta sobre el siguiente post de LinkedIn.\n\n"
            f"POST ACTUAL:\n{post_actual}\n\n"
            f"PREGUNTA DEL USUARIO: {mensaje}\n\n"
            f"Responde de forma directa y concisa."
        )
        expected = "Respuesta directa a la pregunta del usuario sobre el post."

    # Add conversation history as context
    if history:
        history_text = "\n".join(
            f"{'Usuario' if m.get('role') == 'user' else 'Asistente'}: {m.get('content', '')}"
            for m in history
        )
        description = f"HISTORIAL DE CONVERSACION:\n{history_text}\n\n{description}"

    chat_task = Task(
        description=description,
        agent=assistant,
        expected_output=expected,
    )
    chat_crew = Crew(agents=[assistant], tasks=[chat_task], verbose=False)
    chat_result = await _run_crew_async(chat_crew, {})

    return {
        "respuesta": str(chat_result),
        "post_modificado": is_modification,
    }


# ---------------------------------------------------------------------------
# Topic suggestions
# ---------------------------------------------------------------------------

async def suggest_topics() -> list[str]:
    """Returns a list of 5 topic suggestions as strings."""
    topics_crew = Crew(
        agents=[topicSuggester],
        tasks=[topicSuggesterTask],
        verbose=False,
    )
    topics_result = await _run_crew_async(topics_crew, {})
    raw = str(topics_result)

    # Parse individual topic titles from the agent output
    # The agent outputs "IDEA #N — [Title]" format
    topics: list[str] = []
    for line in raw.split("\n"):
        # Match patterns like "IDEA #1 — Title" or "IDEA #1: Title" or "1. Title"
        match = re.match(
            r"(?:IDEA\s*#?\d+\s*[-—:]\s*|^\d+[\.\)]\s*)(.*)",
            line.strip(),
        )
        if match:
            title = match.group(1).strip().strip("*").strip()
            if title and len(title) > 5:
                topics.append(title)

    # Fallback: if parsing fails, split by double newline and take first 5 non-empty blocks
    if len(topics) < 3:
        blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]
        topics = blocks[:5]

    return topics[:5]


# ---------------------------------------------------------------------------
# SSE helper
# ---------------------------------------------------------------------------

def _sse_event(event_type: str, **kwargs: object) -> str:
    data = {"type": event_type, **kwargs}
    return json.dumps(data, ensure_ascii=False)
