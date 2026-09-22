"""Daily scheduling in the configured timezone."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Callable

import pytz
import schedule

import config

logger = logging.getLogger("blogbot")


def next_run_time(now: datetime | None = None) -> datetime:
    """Next occurrence of SCHEDULE_TIME in TIMEZONE."""
    tz = pytz.timezone(config.TIMEZONE)
    now = now or datetime.now(tz)
    hour, minute = (int(part) for part in config.SCHEDULE_TIME.split(":"))
    candidate = tz.localize(datetime(now.year, now.month, now.day, hour, minute))
    if candidate <= now:
        next_day = (now + timedelta(days=1)).date()
        candidate = tz.localize(datetime(next_day.year, next_day.month, next_day.day, hour, minute))
    return candidate


def start(job: Callable[[], object]) -> None:
    """Run `job` every day at SCHEDULE_TIME (TIMEZONE). Blocks until Ctrl+C."""
    schedule.every().day.at(config.SCHEDULE_TIME, config.TIMEZONE).do(job)
    logger.info(
        "Scheduler started, next run: %s (%s)",
        next_run_time().strftime("%Y-%m-%d %H:%M"),
        config.TIMEZONE,
    )
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")
