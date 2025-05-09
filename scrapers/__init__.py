from .base import BaseSourceScraper
from .google_research import GoogleResearchScraper
from .lyft_engineering import LyftEngineeringScraper

# Dictionary mapping source names to their respective scrapers and base URLs
from enum import Enum, auto


class SourceName(str, Enum):
    GOOGLE_RESEARCH = "google_research"
    LYFT_ENGINEERING = "lyft_engineering"


SOURCE_SCRAPERS = {
    SourceName.GOOGLE_RESEARCH.value: GoogleResearchScraper,
    SourceName.LYFT_ENGINEERING.value: LyftEngineeringScraper,
}

__all__ = [
    "BaseSourceScraper",
    "GoogleResearchScraper",
    "LyftEngineeringScraper",
    "SOURCE_SCRAPERS",
]
