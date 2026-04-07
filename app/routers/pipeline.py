import asyncio
import logging

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.core.security import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.pipeline import PipelineRunRequest
from app.services import pipeline_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run")
async def run_pipeline(
    body: PipelineRunRequest,
    _user: dict = Depends(get_current_user),
) -> EventSourceResponse:
    async def event_generator():
        try:
            async for event in pipeline_service.run_pipeline(
                topic=body.topic,
                context=body.context,
            ):
                yield {"data": event}
        except asyncio.CancelledError:
            logger.info("Client disconnected, pipeline cancelled.")

    return EventSourceResponse(event_generator())


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    _user: dict = Depends(get_current_user),
) -> ChatResponse:
    result = await pipeline_service.chat(
        mensaje=body.mensaje,
        post_actual=body.post_actual,
        history=[m.model_dump() for m in body.history],
    )
    return ChatResponse(**result)
