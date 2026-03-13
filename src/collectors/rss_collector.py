"""
RSS / Atom feed collector.

Fetches items published within the last 48 hours from a list of configured
feed URLs and returns them grouped by category.
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser
import requests

logger = logging.getLogger(__name__)

# Request headers that mimic a regular browser to avoid 403s on Chinese sites
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

TIMEOUT = 15  # seconds per request


def _parse_published(entry: feedparser.FeedParserDict) -> Optional[datetime]:
    """Try to extract a timezone-aware published datetime from an entry."""
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    # fallback: raw string fields
    for attr in ("published", "updated"):
        raw = getattr(entry, attr, "")
        if raw:
            try:
                return parsedate_to_datetime(raw).astimezone(timezone.utc)
            except Exception:
                pass
    return None


def _fetch_feed(feed_cfg: dict, cutoff: datetime) -> list[dict]:
    """Fetch a single RSS feed and return items newer than *cutoff*."""
    name = feed_cfg["name"]
    url = feed_cfg["url"]
    category = feed_cfg.get("category", "news")
    items: list[dict] = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
    except Exception as exc:
        logger.warning("Failed to fetch feed '%s' (%s): %s", name, url, exc)
        return items

    for entry in feed.entries:
        pub = _parse_published(entry)
        if pub and pub < cutoff:
            continue  # too old

        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", url)
        summary = (
            getattr(entry, "summary", "")
            or getattr(entry, "description", "")
        )
        # Strip HTML tags from summary
        if summary:
            from html.parser import HTMLParser

            class _Stripper(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self._chunks: list[str] = []

                def handle_data(self, data: str):
                    self._chunks.append(data)

                def get_text(self) -> str:
                    return " ".join(self._chunks).strip()

            stripper = _Stripper()
            stripper.feed(summary)
            summary = stripper.get_text()[:300]

        if title:
            items.append(
                {
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "source": name,
                    "category": category,
                    "published": pub.strftime("%Y-%m-%d") if pub else "N/A",
                }
            )

    logger.info("Feed '%s': collected %d items", name, len(items))
    return items


def collect_rss_feeds(
    feed_configs: list[dict],
    hours_back: int = 48,
    max_per_feed: int = 5,
) -> dict[str, list[dict]]:
    """
    Collect items from all configured RSS feeds.

    Returns a dict keyed by category (e.g. 'papers', 'intl_news',
    'cn_news', 'hardware') with lists of item dicts.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    result: dict[str, list[dict]] = {}

    for feed_cfg in feed_configs:
        items = _fetch_feed(feed_cfg, cutoff)[:max_per_feed]
        cat = feed_cfg.get("category", "news")
        result.setdefault(cat, []).extend(items)
        time.sleep(0.5)  # be polite to servers

    return result
