"""Supabase client and data-access helpers for the curation module."""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any

from supabase import create_client, Client

from app.core.config import settings

# ---------------------------------------------------------------------------
# Singleton client
# ---------------------------------------------------------------------------

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment.")
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def get_active_sources() -> list[dict[str, Any]]:
    """Return all active sources from the `sources` table."""
    response = get_client().table("sources").select("*").eq("active", True).execute()
    return response.data or []


# ---------------------------------------------------------------------------
# Subscribers
# ---------------------------------------------------------------------------

def get_active_subscribers() -> list[str]:
    """Return email addresses of active subscribers."""
    response = (
        get_client()
        .table("subscribers")
        .select("email")
        .eq("active", True)
        .execute()
    )
    return [row["email"] for row in (response.data or [])]


# ---------------------------------------------------------------------------
# Processed topics — deduplication
# ---------------------------------------------------------------------------

def topic_hash(topic_text: str) -> str:
    """SHA-256 hash of a normalized topic string used for deduplication."""
    normalized = topic_text.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


def is_topic_processed(topic_text: str) -> bool:
    """Return True if this topic has already been processed."""
    h = topic_hash(topic_text)
    response = (
        get_client()
        .table("processed_topics")
        .select("id")
        .eq("topic_hash", h)
        .limit(1)
        .execute()
    )
    return bool(response.data)


def save_processed_topic(
    *,
    topic_text: str,
    sources_used: list[dict[str, Any]],
    posts_generated: list[str],
    curation_run_id: str,
) -> None:
    """Insert a processed topic into Supabase to prevent future duplication."""
    get_client().table("processed_topics").insert(
        {
            "topic_hash": topic_hash(topic_text),
            "topic_text": topic_text,
            "sources_used": sources_used,
            "posts_generated": posts_generated,
            "curation_run_id": curation_run_id,
        }
    ).execute()


# ---------------------------------------------------------------------------
# Curation runs — audit log
# ---------------------------------------------------------------------------

def create_curation_run() -> str:
    """Insert a new curation_run row and return its UUID."""
    response = (
        get_client()
        .table("curation_runs")
        .insert({"status": "running", "topics_found": 0, "email_sent": False})
        .execute()
    )
    return response.data[0]["id"]


def update_curation_run(
    run_id: str,
    *,
    status: str,
    topics_found: int = 0,
    email_sent: bool = False,
    error_message: str | None = None,
) -> None:
    """Update an existing curation_run row."""
    payload: dict[str, Any] = {
        "status": status,
        "topics_found": topics_found,
        "email_sent": email_sent,
    }
    if error_message is not None:
        payload["error_message"] = error_message
    get_client().table("curation_runs").update(payload).eq("id", run_id).execute()
