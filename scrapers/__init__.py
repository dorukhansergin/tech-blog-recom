from .base import BaseSourceScraper
from .google_research import GoogleResearchScraper
from .lyft_engineering import LyftEngineeringScraper
from .meta_engineering import MetaEngineeringScraper

# Dictionary mapping source names to their respective scrapers and base URLs
from enum import Enum, auto


class SourceName(str, Enum):
    GOOGLE_RESEARCH = "google_research"
    LYFT_ENGINEERING = "lyft_engineering"
    META_ENGINEERING = "meta_engineering"


SOURCE_SCRAPERS = {
    SourceName.GOOGLE_RESEARCH.value: GoogleResearchScraper,
    SourceName.LYFT_ENGINEERING.value: LyftEngineeringScraper,
    SourceName.META_ENGINEERING.value: MetaEngineeringScraper,
}

__all__ = [
    "BaseSourceScraper",
    "GoogleResearchScraper",
    "LyftEngineeringScraper",
    "MetaEngineeringScraper",
    "SOURCE_SCRAPERS",
]
