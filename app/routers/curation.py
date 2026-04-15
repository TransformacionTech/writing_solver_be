from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sse_starlette.sse import EventSourceResponse
from typing import Any

from app.schemas.curation import (
    CurationTriggerResponse,
    CurationRunOut,
    SourceCreate,
    SourceOut,
    SubscriberCreate,
    SubscriberOut,
)
from app.services import supabase_service as supa

router = APIRouter(prefix="/curation", tags=["curation"])


# ---------------------------------------------------------------------------
# Manual trigger
# ---------------------------------------------------------------------------

@router.post("/run", response_model=CurationTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_curation() -> CurationTriggerResponse:
    """Manually trigger the content curation pipeline."""
    from app.services.curation_service import run_curation

    try:
        result = await run_curation()
        return CurationTriggerResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/run-stream")
async def trigger_curation_stream() -> EventSourceResponse:
    """Manually trigger the curation pipeline with SSE streaming of progress events."""
    from app.services.curation_service import run_curation_stream
    return EventSourceResponse(run_curation_stream())


# ---------------------------------------------------------------------------
# Curation run history
# ---------------------------------------------------------------------------

@router.get("/runs", response_model=list[CurationRunOut])
def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    """Return the last N curation run records."""
    response = (
        supa.get_client()
        .table("curation_runs")
        .select("*")
        .order("run_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


# ---------------------------------------------------------------------------
# Sources CRUD
# ---------------------------------------------------------------------------

@router.get("/sources", response_model=list[SourceOut])
def list_sources() -> list[dict[str, Any]]:
    """Return all active monitoring sources."""
    return supa.get_active_sources()


@router.post("/sources", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
def create_source(body: SourceCreate) -> dict[str, Any]:
    """Add a new monitoring source."""
    response = (
        supa.get_client()
        .table("sources")
        .insert({"name": body.name, "url": body.url})
        .execute()
    )
    return response.data[0]


# ---------------------------------------------------------------------------
# Subscribers CRUD
# ---------------------------------------------------------------------------

@router.get("/subscribers", response_model=list[SubscriberOut])
def list_subscribers() -> list[dict[str, Any]]:
    """Return all active subscribers."""
    response = (
        supa.get_client()
        .table("subscribers")
        .select("*")
        .eq("active", True)
        .execute()
    )
    return response.data or []


@router.post("/subscribers", response_model=SubscriberOut, status_code=status.HTTP_201_CREATED)
def create_subscriber(body: SubscriberCreate) -> dict[str, Any]:
    """Register a new subscriber email."""
    response = (
        supa.get_client()
        .table("subscribers")
        .insert({"email": body.email})
        .execute()
    )
    return response.data[0]
