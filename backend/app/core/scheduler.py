import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.services.job.cleanup import run_cleanup

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> None:
    global _scheduler
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        run_cleanup,
        trigger="interval",
        minutes=settings.cleanup_interval_minutes,
        id="storage_cleanup",
        # Only one cleanup pass should ever run at a time, even if a
        # previous pass is still deleting a very large job directory
        # when the next interval fires.
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    logger.info(
        "cleanup scheduler started",
        extra={"interval_minutes": settings.cleanup_interval_minutes},
    )


def stop_scheduler() -> None:
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        logger.info("cleanup scheduler stopped")