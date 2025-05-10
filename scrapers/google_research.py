from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Iterator, Optional, Tuple
import feedparser
import logging
import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import re

from .base import BaseSourceScraper
from models import BlogEntry


logger = logging.getLogger(__name__)


class GoogleResearchScraper(BaseSourceScraper):
    """Scraper for Google Research blog."""

    feed_url = "https://research.google/blog/rss/"

    def __init__(self):
        """Initialize the scraper with a configured requests session."""
        self.session = requests.Session()
        # Configure retries
        retries = Retry(
            total=3,  # number of retries
            backoff_factor=0.5,  # wait 0.5, 1, 2 seconds between retries
            status_forcelist=[500, 502, 503, 504],  # retry on these HTTP status codes
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # minimum seconds between requests

    def _rate_limit(self):
        """Implement rate limiting."""
        now = time.time()
        time_since_last_request = now - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def _extract_metadata(
        self, soup: BeautifulSoup
    ) -> Tuple[Optional[str], Optional[datetime]]:
        """Extract author and publication date from the page."""
        author = None
        published_date = None

        # Try to find author and date information from the hero description
        description = soup.find("div", class_="basic-hero__description")
        if description:
            text = description.get_text(strip=True)

            # First try to extract the date using a regex pattern
            date_pattern = r"([A-Z][a-z]+ \d{1,2}, \d{4})"
            date_match = re.search(date_pattern, text)

            if date_match:
                try:
                    date_str = date_match.group(1)
                    published_date = datetime.strptime(date_str, "%B %d, %Y")

                    # Get everything after the date
                    author_text = text[date_match.end() :].strip()
                    if author_text.startswith(","):
                        author_text = author_text[1:].strip()

                    # Get the part before the first descriptive comma
                    author = author_text.split(",")[0].strip()

                except (ValueError, IndexError) as e:
                    logger.debug(f"Could not parse date or author: {e}")

        return author, published_date

    def _process_code_blocks(self, soup: BeautifulSoup) -> None:
        """Process and format code blocks in the content."""
        code_blocks = soup.find_all(["pre", "code"])
        for block in code_blocks:
            # Preserve code formatting
            block["data-preserve-formatting"] = True
            # Add newlines around code blocks
            if block.string:
                block.string = f"\n{block.string}\n"

    def _process_images(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract images and their captions."""
        images = []
        media_sections = soup.find_all("div", class_="dynamic_media__item")

        for section in media_sections:
            img = section.find("img")
            caption = section.find_next("div", class_="caption")

            if img:
                image_info = {
                    "url": img.get("src", ""),
                    "alt": img.get("alt", ""),
                    "caption": caption.get_text(strip=True) if caption else "",
                }
                images.append(image_info)

        return images

    def _fetch_full_content(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """Fetch the full content and metadata of a blog post."""
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Process code blocks
            self._process_code_blocks(soup)

            # Extract images
            images = self._process_images(soup)

            # Extract metadata
            author, page_date = self._extract_metadata(soup)

            # Find all content sections
            content_sections = []

            # Get the main content from rich-text sections
            rich_text_sections = soup.find_all("div", class_="rich-text")
            for section in rich_text_sections:
                content_sections.append(section.get_text(separator="\n", strip=True))

            # Get content from component-intro sections
            intro_sections = soup.find_all("div", class_="component-intro")
            for section in intro_sections:
                content_sections.append(section.get_text(separator="\n", strip=True))

            # Get content from blog summary if available
            summary = soup.find("div", class_="blog-summary__summary")
            if summary:
                content_sections.append(summary.get_text(separator="\n", strip=True))

            # Combine all content sections with newlines between them
            content = "\n\n".join(filter(None, content_sections))

            if not content:
                logger.warning(f"Could not find content sections for {url}")
                return "", {}

            metadata = {"author": author, "page_date": page_date, "images": images}

            return content, metadata

        except requests.Timeout:
            logger.error(f"Timeout while fetching content from {url}")
            return "", {}
        except requests.RequestException as e:
            logger.error(f"Error fetching content from {url}: {str(e)}")
            return "", {}

    def scrape(self) -> Iterator[BlogEntry]:
        """Scrape blog entries from Google Research."""
        try:
            feed = feedparser.parse(self.feed_url)
            for entry in feed.entries:
                try:
                    # Extract published date
                    published = datetime(*entry.published_parsed[:6])

                    # Try to get full content from the article page first
                    content, _ = self._fetch_full_content(entry.link)
                    if not content:
                        # Fall back to RSS feed content if full content fetch fails
                        content = entry.get("content", [{}])[0].get("value", "")
                        if not content:
                            content = entry.get("summary", "")

                    yield BlogEntry(
                        title=entry.title,
                        url=entry.link,
                        source="Google Research",
                        published_at=published,
                        content=content,
                    )
                except Exception as e:
                    logger.error(
                        f"Error processing entry {entry.get('link', 'unknown')}: {str(e)}"
                    )
                    continue
        except Exception as e:
            logger.error(f"Error scraping Google Research: {str(e)}")
            raise
