import pytest
from bs4 import BeautifulSoup
from datetime import datetime
from scrapers import LyftEngineeringScraper


@pytest.fixture
def scraper():
    return LyftEngineeringScraper("https://eng.lyft.com/")


@pytest.fixture
def index_html():
    return """
    <html>
        <body>
            <article>
                <a href="/2024/01/test-post-1">Post 1</a>
            </article>
            <article>
                <a href="/2024/02/test-post-2">Post 2</a>
            </article>
            <div class="not-article">
                <a href="/about">About</a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def post_html():
    return """
    <html>
        <body>
            <h1>Test Blog Post Title</h1>
            <time datetime="2024-04-15T10:00:00Z">April 15, 2024</time>
            <div class="author">John Doe</div>
            <article>
                <p>This is the first paragraph.</p>
                <p>This is the second paragraph.</p>
            </article>
        </body>
    </html>
    """


def test_extract_blog_links(scraper):
    """Test that we can extract blog links from the RSS feed."""
    # We don't need a soup object for RSS feeds, but the interface requires it
    soup = BeautifulSoup("", "html.parser")
    links = scraper.extract_blog_links(soup)

    # Verify we got some links
    assert len(links) > 0
    # Verify links are from Lyft Engineering
    assert all("eng.lyft.com" in link for link in links)
    # Verify links are valid URLs
    assert all(link.startswith("https://") for link in links)


def test_extract_metadata(scraper):
    """Test that we can extract metadata from a blog post using the RSS feed."""
    # First get a valid blog post URL
    soup = BeautifulSoup("", "html.parser")
    links = scraper.extract_blog_links(soup)
    assert len(links) > 0
    test_url = links[0]

    # Extract metadata
    metadata = scraper.extract_metadata(soup, test_url)

    # Verify all required fields are present
    assert metadata is not None
    assert "url" in metadata
    assert "title" in metadata
    assert "content" in metadata
    assert "author" in metadata
    assert "published_date" in metadata
    assert "source_name" in metadata

    # Verify field values
    assert metadata["url"] == test_url
    assert isinstance(metadata["title"], str)
    assert len(metadata["title"]) > 0
    assert isinstance(metadata["content"], str)
    assert len(metadata["content"]) > 0
    assert metadata["source_name"] == "Lyft Engineering"
    assert (
        isinstance(metadata["published_date"], datetime)
        or metadata["published_date"] is None
    )


def test_extract_metadata_missing_fields(scraper):
    minimal_html = """
    <html>
        <body>
            <h1>Test Title</h1>
            <article>
                <p>Some content</p>
            </article>
        </body>
    </html>
    """
    soup = BeautifulSoup(minimal_html, "html.parser")
    metadata = scraper.extract_metadata(soup, "https://eng.lyft.com/test-post")

    # Should handle missing fields gracefully
    assert metadata["title"] == "Test Title"
    assert metadata["author"] is None
    assert metadata["published_date"] is None
    assert "Some content" in metadata["content"]
