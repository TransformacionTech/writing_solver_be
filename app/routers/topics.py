from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.schemas.topics import TopicsResponse
from app.services import pipeline_service

router = APIRouter(prefix="/pipeline", tags=["topics"])


@router.get("/suggest-topics", response_model=TopicsResponse)
async def suggest_topics(
    _user: dict = Depends(get_current_user),
) -> TopicsResponse:
    topics = await pipeline_service.suggest_topics()
    return TopicsResponse(topics=topics)
