import logging
from typing import Callable, Optional
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self):
        self._scheduler = BackgroundScheduler()
        self._jobs: dict[str, str] = {}

    def daily(
        self,
        func: Callable,
        hour: int = 8,
        minute: int = 0,
        job_id: Optional[str] = None,
        args: Optional[list] = None,
        kwargs: Optional[dict] = None,
    ) -> str:
        trigger = CronTrigger(hour=hour, minute=minute)
        jid = job_id or f"daily_{func.__name__}"
        self._scheduler.add_job(
            func, trigger, id=jid,
            args=args or [], kwargs=kwargs or {},
            replace_existing=True,
        )
        self._jobs[jid] = "daily"
        logger.info("Scheduled daily job '%s' at %02d:%02d", jid, hour, minute)
        return jid

    def weekly(
        self,
        func: Callable,
        day_of_week: str = "mon",
        hour: int = 9,
        minute: int = 0,
        job_id: Optional[str] = None,
        args: Optional[list] = None,
        kwargs: Optional[dict] = None,
    ) -> str:
        trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        jid = job_id or f"weekly_{func.__name__}"
        self._scheduler.add_job(
            func, trigger, id=jid,
            args=args or [], kwargs=kwargs or {},
            replace_existing=True,
        )
        self._jobs[jid] = "weekly"
        logger.info("Scheduled weekly job '%s' on %s at %02d:%02d", jid, day_of_week, hour, minute)
        return jid

    def custom(
        self,
        func: Callable,
        cron_expr: str,
        job_id: Optional[str] = None,
        args: Optional[list] = None,
        kwargs: Optional[dict] = None,
    ) -> str:
        trigger = CronTrigger.from_crontab(cron_expr)
        jid = job_id or f"custom_{func.__name__}"
        self._scheduler.add_job(
            func, trigger, id=jid,
            args=args or [], kwargs=kwargs or {},
            replace_existing=True,
        )
        self._jobs[jid] = cron_expr
        logger.info("Scheduled custom job '%s' with cron '%s'", jid, cron_expr)
        return jid

    def remove(self, job_id: str) -> None:
        self._scheduler.remove_job(job_id)
        self._jobs.pop(job_id, None)
        logger.info("Removed job: %s", job_id)

    def start(self) -> None:
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started")

    def stop(self) -> None:
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")

    def list_jobs(self) -> list[dict]:
        return [
            {
                "id": job.id,
                "schedule": self._jobs.get(job.id, "unknown"),
                "next_run": getattr(job, "next_run_time", None),
            }
            for job in self._scheduler.get_jobs()
        ]
