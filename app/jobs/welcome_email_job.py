"""
Welcome email job: sends welcome email after user registration.
Rails equivalent: UserMailer.welcome_email.deliver_later
"""

from typing import Any

from config.celery import celery_app
from app.jobs.base_job import BaseJob


@celery_app.task(bind=True, max_retries=5, queue="mailers", name="app.jobs.welcome_email_job.WelcomeEmailJob.run")
def _welcome_email_task(self: Any, **kwargs: Any) -> None:
    """Celery task wrapper for WelcomeEmailJob."""
    try:
        WelcomeEmailJob().perform(**kwargs)
    except Exception as exc:
        WelcomeEmailJob().on_failure(exc, kwargs)
        raise self.retry(exc=exc, countdown=60)


class WelcomeEmailJob(BaseJob):
    """Send welcome email to new user. Queue: mailers, retry_limit: 5."""

    queue = "mailers"
    retry_limit = 5
    _task = _welcome_email_task

    def perform(self, user_id: int, **kwargs: Any) -> None:
        """Fetch user, simulate sending email, log it."""
        from config.database import SessionLocal
        from app.models.user import User
        db = SessionLocal()
        try:
            user = db.get(User, user_id)
            if user:
                print(f"[WelcomeEmailJob] Sending welcome email to {user.email} (id={user_id})")
                # Simulate send - in production: send via SendGrid, SES, etc.
            else:
                print(f"[WelcomeEmailJob] User id={user_id} not found, skipping email")
        finally:
            db.close()

    def on_failure(self, exc: Exception, kwargs: dict[str, Any]) -> None:
        """Log failure with user_id."""
        print(f"[WelcomeEmailJob] FAILED user_id={kwargs.get('user_id')} error={exc}")

    @classmethod
    def perform_later(cls, **kwargs: Any) -> Any:
        """Enqueue to mailers queue."""
        return cls._task.apply_async(kwargs=kwargs, queue=cls.queue)
