import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from datetime import datetime
import random
import time
from scrapers import SOURCE_SCRAPERS


class BlogScraper:
    def __init__(self):
        # More realistic browser headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    def get_source_scraper(self, source_name: str):
        """Get the appropriate source-specific scraper for the source name."""
        if source_name in SOURCE_SCRAPERS:
            source_info = SOURCE_SCRAPERS[source_name]
            return source_info["scraper"](source_info["base_url"])
        return None

    def scrape(self, url: str, source_name: str):
        """Scrape a blog post and return its content."""
        try:
            # Add a small random delay to mimic human behavior
            time.sleep(random.uniform(1, 3))

            # Create a session to maintain cookies
            session = requests.Session()

            # First, try to get the main page to get any necessary cookies
            session.get(url, headers=self.headers, timeout=10)

            # Now make the actual request
            response = session.get(
                url, headers=self.headers, timeout=10, allow_redirects=True
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Get the appropriate source-specific scraper
            source_scraper = self.get_source_scraper(source_name)
            if source_scraper:
                return source_scraper.extract_metadata(soup, url)

            # Fallback to generic scraping if no specific scraper is found
            return self._generic_scrape(soup, url, source_name)

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

    def _generic_scrape(self, soup, url, source_name):
        """Generic scraping method as fallback."""
        # Extract title
        title = soup.find("title")
        title = title.text.strip() if title else "Untitled"

        # Extract main content
        content_containers = [
            soup.find("article"),
            soup.find(class_=re.compile(r"article|post|content|entry", re.I)),
            soup.find(id=re.compile(r"article|post|content|entry", re.I)),
        ]

        content = None
        for container in content_containers:
            if container:
                content = container.get_text(separator="\n", strip=True)
                break

        if not content:
            # Fallback: get all paragraph text
            paragraphs = soup.find_all("p")
            content = "\n".join(p.get_text(strip=True) for p in paragraphs)

        # Extract metadata
        author = self.extract_author(soup)
        published_date = self.extract_date(soup)

        return {
            "url": url,
            "title": title,
            "content": content,
            "author": author,
            "published_date": published_date,
            "source_name": source_name,
        }

    def find_blog_links(self, source_name: str, limit=None):
        """Find blog post links from a source."""
        try:
            # Get source info
            if source_name not in SOURCE_SCRAPERS:
                raise ValueError(f"Unknown source: {source_name}")

            source_info = SOURCE_SCRAPERS[source_name]
            base_url = source_info["base_url"]
            source_scraper = source_info["scraper"](base_url)

            # Add a small random delay to mimic human behavior
            time.sleep(random.uniform(1, 3))

            # Create a session to maintain cookies
            session = requests.Session()
            response = session.get(base_url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            links = source_scraper.extract_blog_links(soup)

            if limit:
                links = links[:limit]

            return links, len(links)

        except Exception as e:
            print(f"Error finding blog links for {source_name}: {str(e)}")
            return [], 0

    def extract_date(self, soup):
        """Extract published date from the blog post."""
        # Common date patterns in blog posts
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
            r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
            r"\d{2}-\d{2}-\d{4}",  # DD-MM-YYYY
        ]

        # Look for date in meta tags
        meta_date = soup.find("meta", property="article:published_time")
        if meta_date:
            try:
                return datetime.fromisoformat(
                    meta_date["content"].replace("Z", "+00:00")
                )
            except:
                pass

        # Look for date in the content
        for pattern in date_patterns:
            date_match = re.search(pattern, str(soup))
            if date_match:
                try:
                    return datetime.strptime(date_match.group(), "%Y-%m-%d")
                except:
                    pass

        return None

    def extract_author(self, soup):
        """Extract author name from the blog post."""
        # Try meta tags first
        author_meta = soup.find("meta", {"property": "article:author"})
        if not author_meta:
            author_meta = soup.find("meta", {"name": "author"})

        if author_meta and author_meta.get("content"):
            return author_meta.get("content")

        # Look for common author patterns in the content
        author_patterns = ["By", "Written by", "Author:", "Posted by"]

        for pattern in author_patterns:
            # Find text containing the pattern
            text_elements = soup.find_all(string=re.compile(pattern, re.IGNORECASE))
            for element in text_elements:
                if element and element.strip():
                    author_text = element.strip()
                    author = re.sub(
                        f"{pattern}\\s*", "", author_text, flags=re.IGNORECASE
                    )
                    if author.strip():
                        return author.strip()

        return None
