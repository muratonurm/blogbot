"""BlogBot CLI entry point."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime

import pytz

import config
import generator
import mailer
import scheduler

logger = logging.getLogger("blogbot")

DEFAULT_PROGRESS = {"last_index": 0, "total_processed": 0, "history": []}


def setup_logging() -> None:
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s", "%Y-%m-%d %H:%M:%S")
    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))
    for handler in (
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ):
        handler.setFormatter(formatter)
        logger.addHandler(handler)


# --- prompts & progress -----------------------------------------------------

def load_prompts() -> list[str]:
    if not config.PROMPTS_FILE.exists():
        return []
    lines = config.PROMPTS_FILE.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def load_progress() -> dict:
    try:
        data = json.loads(config.PROGRESS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return dict(DEFAULT_PROGRESS, history=[])
    except ValueError:
        logger.error("progress.json is corrupted, starting from scratch")
        return dict(DEFAULT_PROGRESS, history=[])
    for key, value in DEFAULT_PROGRESS.items():
        data.setdefault(key, [] if key == "history" else value)
    return data


def save_progress(progress: dict) -> None:
    # Write to a temp file first so a crash never leaves a half-written progress.json
    tmp = config.PROGRESS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(progress, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, config.PROGRESS_FILE)


def now_local() -> datetime:
    return datetime.now(pytz.timezone(config.TIMEZONE))


# --- commands ---------------------------------------------------------------

def run_job(count: int) -> bool:
    """Process `count` prompts starting at last_index. Returns True if at least one succeeded."""
    prompts = load_prompts()
    if not prompts:
        logger.error("No prompts found in %s", config.PROMPTS_FILE.name)
        return False
    if not config.SCRAPE_DO_TOKEN:
        logger.error("SCRAPE_DO_TOKEN is not set in .env")
        return False

    progress = load_progress()
    index = progress["last_index"]
    if not 0 <= index < len(prompts):
        logger.warning("last_index %s is out of range (%s prompts), starting from 0", index, len(prompts))
        index = 0

    count = min(count, len(prompts))
    date_str = now_local().strftime("%Y-%m-%d")
    blogs = []

    logger.info("Starting run: %s prompt(s) from index %s", count, index)
    for step in range(1, count + 1):
        prompt = prompts[index]
        logger.info("Processing prompt %s/%s (prompts.txt #%s)", step, count, index + 1)

        content = generator.generate_blog(prompt)
        entry = {
            "index": index,
            "date": date_str,
            "time": now_local().strftime("%H:%M"),
            "status": "success" if content else "failed",
            "prompt_preview": prompt[:50] + ("..." if len(prompt) > 50 else ""),
        }

        if content:
            title = generator.extract_title(prompt, content)
            path = generator.save_blog(content, title, index + 1, date_str)
            entry["file"] = str(path.relative_to(config.BASE_DIR))
            blogs.append({"title": title, "content": content})
            progress["total_processed"] += 1
            logger.info("Saved: %s (%s words)", entry["file"], len(content.split()))

        progress["history"].append(entry)
        index += 1
        if index >= len(prompts):
            index = 0
            logger.info("All prompts completed, restarting")
        progress["last_index"] = index
        save_progress(progress)  # after every prompt, so an interrupted run resumes correctly

    if blogs:
        mailer.send_email(blogs, date_str)
    else:
        logger.warning("No blogs generated in this run, email not sent")

    logger.info("Run finished: %s/%s succeeded", len(blogs), count)
    return bool(blogs)


def show_status() -> None:
    prompts = load_prompts()
    progress = load_progress()
    history = progress["history"]
    today = now_local().strftime("%Y-%m-%d")

    processed_today = sum(1 for h in history if h.get("date") == today and h.get("status") == "success")
    last_run = f"{history[-1]['date']} {history[-1]['time']}" if history else "Never"
    last_index = progress["last_index"]

    print("BlogBot Status")
    print()
    print(f"Total prompts  : {len(prompts)}")
    print(f"Processed today: {processed_today}")
    print(f"Last run       : {last_run}")
    print(f"Next run       : {scheduler.next_run_time().strftime('%Y-%m-%d %H:%M')}")
    print(f"Last index     : {last_index}")
    print(f"Remaining      : {max(len(prompts) - last_index, 0)}")
    print(f"Total processed: {progress['total_processed']}")


def reset_progress() -> None:
    save_progress(dict(DEFAULT_PROGRESS, history=[]))
    logger.info("Progress reset")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="blogbot",
        description="Generates daily blog posts via Scrape.do ChatGPT plugin and emails them.",
    )
    parser.add_argument("--now", action="store_true", help="run immediately, skip the scheduler")
    parser.add_argument("--status", action="store_true", help="show current progress")
    parser.add_argument("--reset", action="store_true", help="reset progress.json")
    parser.add_argument(
        "--count", type=int, default=config.PROMPTS_PER_RUN,
        help=f"prompts to process per run (default: {config.PROMPTS_PER_RUN})",
    )
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be at least 1")

    if args.status:
        show_status()
        return 0

    setup_logging()

    if args.reset:
        reset_progress()
        return 0

    if args.now:
        return 0 if run_job(args.count) else 1

    scheduler.start(lambda: run_job(args.count))
    return 0


if __name__ == "__main__":
    sys.exit(main())
