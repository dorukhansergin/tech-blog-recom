from datetime import datetime
from typing import Iterator, Optional, Set
import logging
import feedparser
import re
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

from .base import BaseSourceScraper
from models import BlogEntry

logger = logging.getLogger(__name__)


class MetaEngineeringScraper(BaseSourceScraper):
    """Scraper for Meta (Facebook) Engineering blog."""

    rss_feed_url = "https://code.facebook.com/posts/rss/"
    blog_url = "https://engineering.fb.com/"
    graphql_url = "https://engineering.fb.com/wp-json/wp/v2/posts"
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def __init__(self):
        """Initialize the scraper with a configured requests session."""
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
        self.processed_urls = set()

    def _clean_content(self, content: str) -> str:
        """Clean and normalize content."""
        if not content:
            return ""

        # Remove HTML tags
        if bool(BeautifulSoup(content, "html.parser").find()):
            content = BeautifulSoup(content, "html.parser").get_text()

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

    def _extract_date(self, date_str: Optional[str] = None) -> datetime:
        """Extract and validate publish date from string or return current time."""
        if date_str:
            try:
                # Try common date formats
                formats = [
                    "%a, %d %b %Y %H:%M:%S %z",  # RSS feed format
                    "%Y-%m-%dT%H:%M:%S",  # ISO format
                    "%Y-%m-%d %H:%M:%S",  # Common format
                    "%B %d, %Y",  # Blog format
                    "%Y-%m-%d",  # Short ISO format
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue

                logger.warning(f"Could not parse date: {date_str}")
            except Exception as e:
                logger.warning(f"Error parsing date: {str(e)}")

        # Last resort: use current time
        logger.warning("No valid date found, using current time")
        return datetime.utcnow()

    def _process_rss_entry(self, entry) -> Optional[BlogEntry]:
        """Process a single RSS entry into a BlogEntry."""
        try:
            # Skip if we've already processed this URL
            if entry.link in self.processed_urls:
                return None

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

            # Extract date
            published_at = None
            if hasattr(entry, "published"):
                published_at = self._extract_date(entry.published)
            elif hasattr(entry, "updated"):
                published_at = self._extract_date(entry.updated)
            else:
                published_at = datetime.utcnow()

            self.processed_urls.add(entry.link)
            return BlogEntry(
                url=entry.link,
                title=entry.title,
                content=content,
                published_at=published_at,
                source="Meta Engineering",
            )

        except Exception as e:
            logger.error(f"Error processing entry: {str(e)}")
            return None

    def _fetch_graphql_posts(
        self, page: int = 1, per_page: int = 20
    ) -> Iterator[BlogEntry]:
        """Fetch blog posts using the WordPress GraphQL API."""
        try:
            params = {
                "page": page,
                "per_page": per_page,
                "_embed": 1,  # Include embedded content
            }

            response = self.session.get(self.graphql_url, params=params, timeout=30)
            response.raise_for_status()

            posts = response.json()
            if not posts:
                return

            for post in posts:
                try:
                    url = post.get("link")
                    if not url or url in self.processed_urls:
                        continue

                    # Extract content
                    content = post.get("content", {}).get("rendered", "")
                    if not content:
                        content = post.get("excerpt", {}).get("rendered", "")

                    content = self._clean_content(content)

                    # Extract date
                    date_str = post.get("date")
                    published_at = (
                        self._extract_date(date_str) if date_str else datetime.utcnow()
                    )

                    # Create blog entry
                    self.processed_urls.add(url)
                    yield BlogEntry(
                        url=url,
                        title=self._clean_content(
                            post.get("title", {}).get("rendered", "")
                        ),
                        content=content,
                        published_at=published_at,
                        source="Meta Engineering",
                    )

                except Exception as e:
                    logger.error(f"Error processing GraphQL post: {str(e)}")
                    continue

            # Check if there are more pages
            total_pages = int(response.headers.get("X-WP-TotalPages", 1))
            if page < total_pages and page < 5:  # Limit to 5 pages (100 posts)
                yield from self._fetch_graphql_posts(page + 1, per_page)

        except Exception as e:
            logger.error(f"Error fetching GraphQL posts: {str(e)}")

    def scrape(self) -> Iterator[BlogEntry]:
        """Scrape Meta Engineering blog posts from both RSS feed and GraphQL API."""
        try:
            # First try RSS feed
            logger.info(f"Fetching feed from {self.rss_feed_url}")
            feed = feedparser.parse(self.rss_feed_url)

            if self._validate_feed(feed):
                for entry in feed.entries:
                    blog_entry = self._process_rss_entry(entry)
                    if blog_entry:
                        yield blog_entry

            # Then fetch posts from GraphQL API
            logger.info("Fetching posts from GraphQL API")
            yield from self._fetch_graphql_posts()

        except Exception as e:
            logger.error(f"Failed to scrape Meta Engineering blog: {str(e)}")
            raise

        finally:
            self.last_scrape_time = datetime.now()
