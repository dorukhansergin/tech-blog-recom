from datetime import datetime
from typing import Iterator, Optional
import logging
import feedparser
import re

from .base import BaseSourceScraper
from models import BlogEntry

logger = logging.getLogger(__name__)


class MetaEngineeringScraper(BaseSourceScraper):
    """Scraper for Meta (Facebook) Engineering blog."""

    feed_url = "https://code.facebook.com/posts/rss/"

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        if not content:
            return ""

        # Remove extra whitespace
        content = " ".join(content.split())

        # Remove common boilerplate
        content = content.replace("Read More...", "")
        content = content.replace("The post", "")
        content = content.replace("appeared first on Engineering at Meta.", "")

        return content.strip()

    def _validate_feed(self, feed: feedparser.FeedParserDict) -> bool:
        """Validate the RSS feed structure."""
        if not hasattr(feed, "entries"):
            logger.error("Feed has no entries")
            return False

        if not feed.entries:
            logger.warning("Feed has empty entries")
            return False

        # Check if feed is in error state
        if hasattr(feed, "bozo") and feed.bozo:
            logger.error(f"Feed parsing error: {feed.bozo_exception}")
            return False

        # Validate feed title and link
        if not hasattr(feed.feed, "title") or not hasattr(feed.feed, "link"):
            logger.error("Feed missing required fields (title or link)")
            return False

        return True

    def _extract_date(self, entry) -> datetime:
        """Extract and validate publish date from entry.

        Tries multiple date fields and falls back to current time if none are valid.
        """
        # Try published_parsed first (struct_time)
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])

        # Try published (string)
        if hasattr(entry, "published"):
            try:
                # Try parsing the string directly
                return datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                logger.warning(f"Could not parse published date: {entry.published}")

        # Try updated fields as fallback
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return datetime(*entry.updated_parsed[:6])

        if hasattr(entry, "updated"):
            try:
                return datetime.strptime(entry.updated, "%a, %d %b %Y %H:%M:%S %z")
            except ValueError:
                logger.warning(f"Could not parse updated date: {entry.updated}")

        # Last resort: use current time
        logger.warning("No valid date found, using current time")
        return datetime.utcnow()

    def _process_entry(self, entry) -> Optional[BlogEntry]:
        """Process a single RSS entry into a BlogEntry."""
        try:
            # Validate required fields
            if not all(hasattr(entry, attr) for attr in ["title", "link"]):
                logger.warning(
                    f"Entry missing required fields: {entry.get('link', 'unknown')}"
                )
                return None

            # Get content
            content = entry.get("summary", "")
            if hasattr(entry, "content"):
                content = entry.content[0].value

            # Clean content
            content = self._clean_content(content)

            # Basic validation
            if not content or not entry.title:
                logger.warning(f"Invalid content for entry: {entry.link}")
                return None

            return BlogEntry(
                url=entry.link,
                title=entry.title,
                content=content,
                published_at=self._extract_date(entry),
                source="Meta Engineering",
            )

        except Exception as e:
            logger.error(f"Error processing entry: {str(e)}")
            return None

    def scrape(self) -> Iterator[BlogEntry]:
        """Scrape Meta Engineering blog posts from RSS feed."""
        try:
            logger.info(f"Fetching feed from {self.feed_url}")
            feed = feedparser.parse(self.feed_url)

            if not self._validate_feed(feed):
                raise ValueError("Invalid feed structure")

            entry_count = 0
            for entry in feed.entries:
                blog_entry = self._process_entry(entry)
                if blog_entry:
                    entry_count += 1
                    yield blog_entry

            logger.info(f"Successfully processed {entry_count} entries from feed")

        except Exception as e:
            logger.error(f"Failed to parse Meta Engineering RSS feed: {str(e)}")
            raise

        finally:
            self.last_scrape_time = datetime.now()
