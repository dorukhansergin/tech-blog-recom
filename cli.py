import click
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, List
from scrapers import SOURCE_SCRAPERS, SourceName
from models import BlogEntry, ProcessedBlogEntry
import os
from pathlib import Path
import time
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT


def process_entry(
    entry: BlogEntry, model: SentenceTransformer, keyword_model: KeyBERT
) -> ProcessedBlogEntry:
    """Process a blog entry to generate embeddings and keywords."""
    # Generate embedding
    embedding = model.encode(entry.content)

    # Extract keywords
    keywords = keyword_model.extract_keywords(
        entry.content, keyphrase_ngram_range=(1, 2), stop_words="english", top_n=5
    )
    keywords = [k[0] for k in keywords]  # Extract just the keywords from tuples

    return ProcessedBlogEntry(
        title=entry.title,
        url=entry.url,
        source=entry.source,
        published_at=entry.published_at,
        content=entry.content,
        embedding=embedding,
        keywords=keywords,
    )


@click.group()
def cli():
    """Blog post scraper CLI."""
    pass


@cli.command()
@click.option(
    "--sources",
    "-s",
    type=click.Choice(list(SOURCE_SCRAPERS.keys())),
    multiple=True,
    required=True,
    help="Source names to scrape (e.g., 'google_research', 'lyft_engineering'). Can specify multiple times.",
)
@click.option(
    "--limit", "-l", type=int, help="Maximum number of posts to scrape per source"
)
@click.option(
    "--output",
    "-o",
    type=str,
    default="combined",
    help="Output filename prefix (without extension)",
)
def scrape(sources: List[str], limit: Optional[int], output: str):
    """Scrape blog posts from multiple sources and combine them into a single file."""

    # Initialize models
    model = SentenceTransformer("all-MiniLM-L6-v2")
    keyword_model = KeyBERT()

    # Create output directory if it doesn't exist
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    all_entries = []

    for source in sources:
        click.echo(f"\nProcessing source: {source}")

        # Initialize scraper
        scraper = SOURCE_SCRAPERS[source]()

        # Collect entries
        for i, entry in enumerate(scraper.scrape()):
            if limit and i >= limit:
                break

            try:
                processed_entry = process_entry(entry, model, keyword_model)
                all_entries.append(processed_entry)
                click.echo(f"Processed ({i + 1}): {entry.title}")

                # Add a small delay between requests
                time.sleep(0.5)

            except Exception as e:
                click.echo(f"Error processing {entry.url}: {str(e)}")

    if not all_entries:
        click.echo("No blog posts found.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(
        [
            {
                "title": e.title,
                "url": e.url,
                "source": e.source,
                "published_at": e.published_at,
                "content": e.content,
                "embedding": e.embedding,
                "keywords": e.keywords,
            }
            for e in all_entries
        ]
    )

    # Save to parquet
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{output}_{timestamp}.parquet"
    df.to_parquet(output_file)

    click.echo(f"\nSaved {len(all_entries)} entries to {output_file}")


if __name__ == "__main__":
    cli()
