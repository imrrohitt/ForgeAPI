"""
Cleanup job: permanently delete soft-deleted posts older than 30 days.
Rails equivalent: cron job / sidekiq-cron
"""

from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select

from config.celery import celery_app
from app.jobs.base_job import BaseJob


@celery_app.task(bind=True, max_retries=3, queue="low_priority", name="app.jobs.cleanup_job.CleanupJob.run")
def _cleanup_task(self: Any, **kwargs: Any) -> dict[str, Any]:
    """Celery task wrapper for CleanupJob."""
    try:
        return CleanupJob().perform(**kwargs)
    except Exception as exc:
        CleanupJob().on_failure(exc, kwargs)
        raise self.retry(exc=exc, countdown=60)


class CleanupJob(BaseJob):
    """Delete soft-deleted posts older than 30 days. Queue: low_priority. Run via Beat daily."""

    queue = "low_priority"
    _task = _cleanup_task

    def perform(self, **kwargs: Any) -> dict[str, Any]:
        """Delete posts where deleted_at < 30 days ago."""
        from config.database import SessionLocal
        from app.models.post import Post
        db = SessionLocal()
        try:
            threshold = datetime.now(timezone.utc) - timedelta(days=30)
            stmt = select(Post).where(Post.deleted_at.isnot(None), Post.deleted_at < threshold)
            to_delete = list(db.execute(stmt).scalars().all())
            count = 0
            for post in to_delete:
                db.delete(post)
                count += 1
            db.commit()
            print(f"[CleanupJob] Permanently deleted {count} soft-deleted posts older than 30 days")
            return {"deleted": count}
        finally:
            db.close()

    @classmethod
    def perform_later(cls, **kwargs: Any) -> Any:
        """Enqueue to low_priority queue."""
        return cls._task.apply_async(kwargs=kwargs, queue=cls.queue)
