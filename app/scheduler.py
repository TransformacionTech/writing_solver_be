"""APScheduler setup — runs the curation pipeline every 15 days."""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _curation_job() -> None:
    from app.services.curation_service import run_curation

    logger.info("Curation job started.")
    try:
        result = await run_curation()
        logger.info("Curation job finished: %s", result)
    except Exception:
        logger.exception("Curation job failed.")


def start_scheduler() -> None:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _curation_job,
        trigger=IntervalTrigger(days=15),
        id="curation_job",
        name="Content curation every 15 days",
        replace_existing=True,
        misfire_grace_time=3600,  # 1 hour grace window
    )
    _scheduler.start()
    logger.info("Scheduler started — curation every 15 days.")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
