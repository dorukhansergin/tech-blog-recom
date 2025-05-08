# Tech Blog Scraper

A Python tool for scraping and managing blog posts from various tech company blogs.

## Features

- Scrape blog posts from multiple sources:
  - Google Research Blog
  - All Things Distributed (Werner Vogels' blog)
  - Martin Kleppmann's Blog
  - Lyft Engineering Blog
- Parallel scraping with configurable number of workers
- Export posts in JSON or CSV format
- Filter posts by company, author, and date range
- Store posts in SQLite database
- Source-specific scraping logic for better accuracy

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tech-blog-scraper.git
cd tech-blog-scraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Scraping Blog Posts

Scrape posts from multiple sources:
```bash
python cli.py scrape https://research.google/blog/ https://www.allthingsdistributed.com/articles.html --limit 10 --output exports
```

Options:
- `--limit`, `-l`: Maximum number of posts to scrape per source
- `--output`, `-o`: Directory to save JSON files
- `--workers`, `-w`: Number of worker threads for parallel scraping (default: 4)

### Listing Posts

List all scraped posts:
```bash
python cli.py list
```

Filter posts:
```bash
python cli.py list --company "Google Research" --author "John Doe" --date-from "2024-01-01" --date-to "2024-12-31"
```

### Exporting Posts

Export posts to JSON:
```bash
python cli.py export --format json --output posts.json
```

Export posts to CSV:
```bash
python cli.py export --format csv --output posts.csv
```

Filter exports:
```bash
python cli.py export --format json --output posts.json --company "Google Research" --date-from "2024-01-01"
```

## Database Schema

The SQLite database (`blog_posts.db`) contains a single table `posts` with the following columns:

- `id`: Unique identifier
- `url`: Blog post URL (unique)
- `title`: Post title
- `content`: Post content
- `author`: Author name
- `published_date`: Publication date
- `company`: Company name
- `created_at`: When the post was scraped

## Adding New Sources

To add a new blog source:

1. Create a new scraper class in `source_scrapers.py` that inherits from `BaseSourceScraper`
2. Implement the required methods:
   - `extract_blog_links`: Extract blog post links from the index page
   - `extract_metadata`: Extract metadata from a blog post
3. Add the new scraper to the `SOURCE_SCRAPERS` dictionary in `source_scrapers.py`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 