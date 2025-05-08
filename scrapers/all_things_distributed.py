from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any

from .base import BaseSourceScraper


class AllThingsDistributedScraper(BaseSourceScraper):
    """Scraper for All Things Distributed blog."""

    def extract_blog_links(self, soup: BeautifulSoup) -> List[str]:
        links = []
        # Find all blog post elements using itemProp attribute
        blog_posts = soup.find_all(attrs={"itemprop": "blogPost"})
        for post in blog_posts:
            link = post.find("a", href=True)
            if link and link["href"]:
                full_url = urljoin(self.base_url, link["href"])
                links.append(full_url)
        return links

    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        # Try multiple methods to find the title
        title = None

        # Method 1: Try meta tags first
        meta_title = soup.find("meta", property="og:title")
        if meta_title and meta_title.get("content"):
            title = meta_title["content"]

        # Method 2: Try itemprop name
        if not title:
            meta_name = soup.find("meta", itemprop="name")
            if meta_name and meta_name.get("content"):
                title = meta_name["content"]

        # Method 3: Try JSON-LD
        if not title:
            script = soup.find("script", type="application/ld+json")
            if script:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict) and "headline" in json_data:
                        title = json_data["headline"]
                except:
                    pass

        # Method 4: Try h1 tag as fallback
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.text.strip()

        # Method 5: Try title tag as last resort
        if not title:
            title_tag = soup.find("title")
            if title_tag:
                # Remove the " | All Things Distributed" suffix if present
                title = title_tag.text.split(" | ")[0].strip()

        # If all methods fail, use "Untitled"
        title = title or "Untitled"

        # Extract date from the article header
        date_elem = soup.find("time")
        published_date = None
        if date_elem:
            try:
                # The date format is like "April 09, 2025"
                date_text = date_elem.text.strip()
                published_date = datetime.strptime(date_text, "%B %d, %Y")
            except:
                pass

        # Author is always Werner Vogels
        author = "Werner Vogels"

        # Extract content from the article body
        content_elem = soup.find("article")
        if not content_elem:
            content_elem = soup.find("div", class_="post-content")

        content = ""
        if content_elem:
            # Get all text content, excluding navigation and footer
            paragraphs = content_elem.find_all("p")
            content = "\n".join(p.text.strip() for p in paragraphs if p.text.strip())

        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "published_date": published_date,
            "source_name": "AllThingsDistributed",
        }
