from .base import BaseSourceScraper
from .google_research import GoogleResearchScraper
from .all_things_distributed import AllThingsDistributedScraper
from .kleppmann import KleppmannScraper
from .lyft_engineering import LyftEngineeringScraper

# Dictionary mapping source names to their respective scrapers and base URLs
SOURCE_SCRAPERS = {
    "Google Research": {
        "scraper": GoogleResearchScraper,
        "base_url": "https://research.google/blog/",
    },
    "AllThingsDistributed": {
        "scraper": AllThingsDistributedScraper,
        "base_url": "https://www.allthingsdistributed.com/articles.html",
    },
    "Martin Kleppmann": {
        "scraper": KleppmannScraper,
        "base_url": "https://martin.kleppmann.com/",
    },
    "Lyft Engineering": {
        "scraper": LyftEngineeringScraper,
        "base_url": "https://eng.lyft.com/",
    },
}

__all__ = [
    "BaseSourceScraper",
    "GoogleResearchScraper",
    "AllThingsDistributedScraper",
    "KleppmannScraper",
    "LyftEngineeringScraper",
    "SOURCE_SCRAPERS",
]
