from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import List, Iterator
from models import BlogEntry
import requests
from datetime import datetime


class BaseSourceScraper(ABC):
    """Base class for source-specific scrapers."""

    @abstractmethod
    def scrape(self) -> Iterator[BlogEntry]:
        """Main scraping method that yields BlogEntry objects."""
        pass
