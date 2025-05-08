from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from .base import BaseSourceScraper


class KleppmannScraper(BaseSourceScraper):
    """Scraper for Martin Kleppmann's blog."""

    def extract_blog_links(self, soup: BeautifulSoup) -> List[str]:
        links = []
        # Martin's blog links are in the archive list
        archive_items = soup.find_all("li", class_="archive-item")
        for item in archive_items:
            link = item.find("a", href=True)
            if link and link["href"]:
                full_url = urljoin(self.base_url, link["href"])
                links.append(full_url)
        return links

    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        title = soup.find("h1")
        title = title.text.strip() if title else "Untitled"

        # Extract date from the header
        date_elem = soup.find("div", class_="date")
        published_date = None
        if date_elem:
            try:
                published_date = datetime.strptime(date_elem.text.strip(), "%d %B %Y")
            except:
                pass

        # Author is always Martin Kleppmann
        author = "Martin Kleppmann"

        # Extract content
        content_elem = soup.find("div", class_="post")
        content = (
            content_elem.get_text(separator="\n", strip=True) if content_elem else ""
        )

        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "published_date": published_date,
            "source_name": "Martin Kleppmann",
        }
