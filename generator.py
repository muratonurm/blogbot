"""Scrape.do ChatGPT plugin integration: request, parse and clean blog content."""

from __future__ import annotations

import logging
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

import config

logger = logging.getLogger("blogbot")


def clean_markdown(markdown: str) -> str:
    """Remove ':::' blocks (citations/widgets) and stray code fences."""
    content = re.sub(r":::.*?:::", "", markdown, flags=re.DOTALL)
    content = re.sub(r":::.*", "", content)
    content = content.strip()

    # ChatGPT sometimes wraps the whole post in ```markdown ... ```
    fenced = re.fullmatch(r"```(?:markdown|md)?\s*\n(.*)\n```", content, flags=re.DOTALL)
    if fenced:
        content = fenced.group(1).strip()
    return content


def _save_raw_response(text: str) -> Path:
    config.RAW_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    path = config.RAW_OUTPUT_PATH / f"{datetime.now():%Y-%m-%d_%H%M%S}_raw.txt"
    path.write_text(text, encoding="utf-8")
    return path


def _is_retryable(status_code: int) -> bool:
    # 429 and 5xx are temporary; other 4xx (e.g. 401 bad token) would fail forever
    return status_code == 429 or status_code >= 500


def _request_with_retry(params: dict) -> requests.Response:
    """GET the Scrape.do endpoint, retrying every RETRY_DELAY seconds until it succeeds.

    Timeouts, connection errors, HTTP 429 and HTTP 5xx are retried. Any other
    response is returned as is, so the caller's error handling still applies.
    """
    attempt = 1
    while True:
        try:
            response = requests.get(config.API_URL, params=params, timeout=config.REQUEST_TIMEOUT)
        except requests.exceptions.Timeout:
            reason = f"timeout after {config.REQUEST_TIMEOUT}s"
        except requests.exceptions.RequestException as exc:
            reason = f"request error: {exc}"
        else:
            if not _is_retryable(response.status_code):
                if response.status_code == 200:
                    logger.info("Succeeded on attempt %s", attempt)
                return response
            reason = f"HTTP {response.status_code}"

        logger.warning("Attempt %s failed (%s), retrying in %ss...", attempt, reason, config.RETRY_DELAY)
        time.sleep(config.RETRY_DELAY)
        attempt += 1


def generate_blog(prompt: str) -> str | None:
    """Send the prompt to Scrape.do and return cleaned markdown, or None on failure."""
    params = {"token": config.SCRAPE_DO_TOKEN, "q": prompt}
    response = _request_with_retry(params)

    if response.status_code != 200:
        logger.error(
            "Scrape.do returned HTTP %s: %s", response.status_code, response.text[:300]
        )
        return None

    try:
        data = response.json()
    except ValueError:
        path = _save_raw_response(response.text)
        logger.error("Could not parse JSON response, raw response saved to %s", path)
        return None

    output = data.get("output") if isinstance(data, dict) else None
    if not isinstance(output, dict):
        logger.error("Response has no 'output' key, skipping prompt")
        return None

    markdown = output.get("markdown")
    if not markdown:
        logger.error("Response has no 'output.markdown' content, skipping prompt")
        return None

    content = clean_markdown(markdown)
    if not content:
        logger.error("Content is empty after cleaning, skipping prompt")
        return None
    return content


def extract_title(prompt: str, content: str) -> str:
    """Title from the prompt ('titled "..."'), else first markdown heading, else prompt start."""
    match = re.search(r"titled\s+[\"'“‘](.+?)[\"'”’](?=[.,;:\s]|$)", prompt, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()

    heading = re.search(r"^#{1,3}\s+(.+)$", content, flags=re.MULTILINE)
    if heading:
        return heading.group(1).strip().strip("*")

    return " ".join(prompt.split()[:8])


def slugify(text: str, max_words: int = 5) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    words = re.findall(r"[a-z0-9]+", text.lower())
    return "-".join(words[:max_words]) or "blog"


def save_blog(content: str, title: str, number: int, date_str: str) -> Path:
    """Write the post to output/{date}_blog_{number}_{slug}.md and return its path."""
    config.OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    path = config.OUTPUT_PATH / f"{date_str}_blog_{number}_{slugify(title)}.md"
    path.write_text(content + "\n", encoding="utf-8")
    return path
