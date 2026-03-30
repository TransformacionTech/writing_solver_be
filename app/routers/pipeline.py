from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.core.security import get_current_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.pipeline import PipelineRunRequest
from app.services import pipeline_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/run")
async def run_pipeline(
    body: PipelineRunRequest,
    _user: dict = Depends(get_current_user),
) -> EventSourceResponse:
    async def event_generator():
        async for event in pipeline_service.run_pipeline(
            topic=body.topic,
            context=body.context,
        ):
            yield {"data": event}

    return EventSourceResponse(event_generator())


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    _user: dict = Depends(get_current_user),
) -> ChatResponse:
    reply = await pipeline_service.chat(
        message=body.message,
        history=body.history,
    )
    return ChatResponse(reply=reply)
