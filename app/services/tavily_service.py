"""Tavily search helpers for the curation module."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from tavily import TavilyClient

from app.core.config import settings

_client: TavilyClient | None = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        if not settings.tavily_api_key:
            raise RuntimeError("TAVILY_API_KEY must be set in environment.")
        _client = TavilyClient(api_key=settings.tavily_api_key)
    return _client


def search_source_news(source_url: str, days: int = 15) -> list[dict[str, Any]]:
    """
    Search for recent articles from a given source URL.

    Returns a list of dicts with keys: title, url, content, published_date.
    Only includes results published within the last `days` days.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        response = _get_client().search(
            query=f"site:{source_url} noticias seguros insurtech LATAM",
            search_depth="advanced",
            max_results=5,
            include_raw_content=False,
        )
    except Exception:
        return []

    results: list[dict[str, Any]] = []
    for item in response.get("results", []):
        published_raw: str | None = item.get("published_date")
        published_dt: datetime | None = None

        if published_raw:
            try:
                published_dt = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Skip if older than cutoff (only filter when date is available)
        if published_dt and published_dt < cutoff:
            continue

        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "published_date": published_raw or "",
                "source": source_url,
            }
        )

    return results


def search_topic_news(topic: str, days: int = 15) -> list[dict[str, Any]]:
    """
    General search for a topic across the web, filtered to the last `days` days.
    Used when we already know the topic and want to enrich the context for the writer.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    try:
        response = _get_client().search(
            query=f"{topic} seguros aseguradoras LATAM {datetime.now().year}",
            search_depth="advanced",
            max_results=5,
            include_raw_content=False,
        )
    except Exception:
        return []

    results: list[dict[str, Any]] = []
    for item in response.get("results", []):
        published_raw: str | None = item.get("published_date")
        published_dt: datetime | None = None

        if published_raw:
            try:
                published_dt = datetime.fromisoformat(published_raw.replace("Z", "+00:00"))
            except ValueError:
                pass

        if published_dt and published_dt < cutoff:
            continue

        results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "published_date": published_raw or "",
                "source": item.get("url", ""),
            }
        )

    return results
