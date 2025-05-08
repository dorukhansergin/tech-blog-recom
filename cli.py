import click
import json
from scraper import BlogScraper
from database import Database
import os
from datetime import datetime
from typing import List, Optional
import concurrent.futures
import time
from scrapers import SOURCE_SCRAPERS


@click.group()
def cli():
    """Blog post scraper CLI."""
    pass


@cli.command()
@click.option(
    "--sources",
    "-s",
    multiple=True,
    help="Source names to scrape (e.g., 'Google Research', 'AllThingsDistributed'). If not specified, all sources will be scraped.",
)
@click.option(
    "--limit", "-l", type=int, help="Maximum number of posts to scrape per source"
)
@click.option("--output", "-o", type=str, help="Output directory for JSON files")
@click.option(
    "--workers",
    "-w",
    type=int,
    default=4,
    help="Number of worker threads for parallel scraping",
)
def scrape(
    sources: Optional[List[str]],
    limit: Optional[int],
    output: Optional[str],
    workers: int,
):
    """Scrape blog posts from multiple sources."""
    scraper = BlogScraper()
    db = Database()

    # Create output directory if specified
    if output:
        os.makedirs(output, exist_ok=True)

    # If no sources specified, use all available sources
    if not sources:
        sources = list(SOURCE_SCRAPERS.keys())

    # Process each source
    for source_name in sources:
        if source_name not in SOURCE_SCRAPERS:
            click.echo(f"\nUnknown source: {source_name}. Skipping...")
            continue

        click.echo(f"\nProcessing source: {source_name}")

        # Find blog post links
        links, total_links = scraper.find_blog_links(source_name, limit)
        click.echo(f"Found {len(links)} blog posts to scrape")

        if not links:
            click.echo("No blog posts found. Skipping...")
            continue

        # Scrape posts in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_url = {
                executor.submit(scraper.scrape, url, source_name): url for url in links
            }

            for i, future in enumerate(
                concurrent.futures.as_completed(future_to_url), 1
            ):
                url = future_to_url[future]
                try:
                    post_data = future.result()
                    if post_data:
                        # Save to database
                        db.save_post(post_data)

                        # Save to JSON file if output directory is specified
                        if output:
                            filename = f"{post_data['source_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.json"
                            filepath = os.path.join(output, filename)
                            with open(filepath, "w", encoding="utf-8") as f:
                                json.dump(post_data, f, indent=2, default=str)

                        click.echo(f"Scraped ({i}/{len(links)}): {post_data['title']}")
                    else:
                        click.echo(f"Failed to scrape: {url}")
                except Exception as e:
                    click.echo(f"Error processing {url}: {str(e)}")

                # Add a small delay between requests to be nice to the servers
                time.sleep(0.5)

    click.echo("\nScraping completed!")


@cli.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "csv"]),
    default="json",
    help="Export format",
)
@click.option("--output", "-o", type=str, required=True, help="Output file path")
@click.option("--source", "-s", type=str, help="Filter by source name")
@click.option("--author", "-a", type=str, help="Filter by author")
@click.option("--date-from", type=str, help="Filter by start date (YYYY-MM-DD)")
@click.option("--date-to", type=str, help="Filter by end date (YYYY-MM-DD)")
def export(
    format: str,
    output: str,
    source: Optional[str],
    author: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
):
    """Export scraped blog posts."""
    db = Database()

    # Build query filters
    filters = {}
    if source:
        filters["source_name"] = source
    if author:
        filters["author"] = author
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    # Get posts from database
    posts = db.get_posts(filters)

    if not posts:
        click.echo("No posts found matching the criteria.")
        return

    # Export in specified format
    if format == "json":
        with open(output, "w", encoding="utf-8") as f:
            json.dump(posts, f, indent=2, default=str)
    else:  # csv
        import csv

        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "url",
                    "title",
                    "content",
                    "author",
                    "published_date",
                    "source_name",
                ],
            )
            writer.writeheader()
            for post in posts:
                writer.writerow(post)

    click.echo(f"Exported {len(posts)} posts to {output}")


@cli.command()
@click.option("--source", "-s", type=str, help="Filter by source name")
@click.option("--author", "-a", type=str, help="Filter by author")
@click.option("--date-from", type=str, help="Filter by start date (YYYY-MM-DD)")
@click.option("--date-to", type=str, help="Filter by end date (YYYY-MM-DD)")
def list(
    source: Optional[str],
    author: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
):
    """List scraped blog posts."""
    db = Database()

    # Build query filters
    filters = {}
    if source:
        filters["source_name"] = source
    if author:
        filters["author"] = author
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to

    # Get posts from database
    posts = db.get_posts(filters)

    if not posts:
        click.echo("No posts found matching the criteria.")
        return

    # Display posts
    for post in posts:
        click.echo("\n" + "=" * 80)
        click.echo(f"Title: {post['title']}")
        click.echo(f"Author: {post['author']}")
        click.echo(f"Source: {post['source_name']}")
        click.echo(f"Date: {post['published_date']}")
        click.echo(f"URL: {post['url']}")
        click.echo("=" * 80)

    click.echo(f"\nTotal posts: {len(posts)}")


if __name__ == "__main__":
    cli()
