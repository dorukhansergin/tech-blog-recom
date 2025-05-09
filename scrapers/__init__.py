from .base import BaseSourceScraper
from .google_research import GoogleResearchScraper
from .all_things_distributed import AllThingsDistributedScraper
from .kleppmann import KleppmannScraper
from .lyft_engineering import LyftEngineeringScraper

# Dictionary mapping source names to their respective scrapers and base URLs
from enum import Enum, auto


class SourceName(str, Enum):
    GOOGLE_RESEARCH = "google_research"
    ALL_THINGS_DISTRIBUTED = "all_things_distributed"
    MARTIN_KLEPPMANN = "martin_kleppmann"
    LYFT_ENGINEERING = "lyft_engineering"


SOURCE_SCRAPERS = {
    SourceName.GOOGLE_RESEARCH.value: GoogleResearchScraper,
    SourceName.ALL_THINGS_DISTRIBUTED.value: AllThingsDistributedScraper,
    SourceName.MARTIN_KLEPPMANN.value: KleppmannScraper,
    SourceName.LYFT_ENGINEERING.value: LyftEngineeringScraper,
}

__all__ = [
    "BaseSourceScraper",
    "GoogleResearchScraper",
    "AllThingsDistributedScraper",
    "KleppmannScraper",
    "LyftEngineeringScraper",
    "SOURCE_SCRAPERS",
]
