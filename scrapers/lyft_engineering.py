from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List, Dict, Any

from .base import BaseSourceScraper


class LyftEngineeringScraper(BaseSourceScraper):
    """Scraper for Lyft Engineering blog."""

    def extract_blog_links(self, soup: BeautifulSoup) -> List[str]:
        links = []
        # Lyft Engineering blog links are in article elements
        articles = soup.find_all("article")
        for article in articles:
            link = article.find("a", href=True)
            if link and link["href"]:
                full_url = urljoin(self.base_url, link["href"])
                links.append(full_url)
        return links

    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        title = soup.find("h1")
        title = title.text.strip() if title else "Untitled"

        # Extract date
        date_elem = soup.find("time")
        published_date = None
        if date_elem and date_elem.get("datetime"):
            try:
                published_date = datetime.fromisoformat(
                    date_elem["datetime"].replace("Z", "+00:00")
                )
            except:
                pass

        # Extract author
        author_elem = soup.find("div", class_="author")
        author = author_elem.text.strip() if author_elem else None

        # Extract content
        content_elem = soup.find("article")
        content = (
            content_elem.get_text(separator="\n", strip=True) if content_elem else ""
        )

        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "published_date": published_date,
            "source_name": "Lyft Engineering",
        }
