from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Iterator
import feedparser
import logging

from .base import BaseSourceScraper
from models import BlogEntry


logger = logging.getLogger(__name__)


class LyftEngineeringScraper(BaseSourceScraper):
    """Scraper for Lyft Engineering blog."""

    feed_url = "https://medium.com/feed/lyft-engineering"

    def scrape(self) -> Iterator[BlogEntry]:
        """Main scraping method that yields BlogEntry objects from the RSS feed."""
        feed = feedparser.parse(self.feed_url)

        for entry in feed.entries:
            # Parse published date
            published_date = None
            if hasattr(entry, "published_parsed"):
                published_date = datetime(*entry.published_parsed[:6])

            content = (
                entry.get("content", [{"value": ""}])[0]["value"]
                if hasattr(entry, "content")
                else entry.get("summary", "")
            )

            if not content:
                logger.debug(f"Empty content found for entry: {entry.link}")

            yield BlogEntry(
                url=entry.link,
                title=entry.title,
                content=content,
                published_at=published_date,
                source="Lyft Engineering",
            )
