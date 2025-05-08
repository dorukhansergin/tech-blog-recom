from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import List, Dict, Any


class BaseSourceScraper(ABC):
    """Base class for source-specific scrapers."""

    def __init__(self, base_url: str):
        self.base_url = base_url

    @abstractmethod
    def extract_blog_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract blog post links from the index page."""
        pass

    @abstractmethod
    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from a blog post."""
        pass
