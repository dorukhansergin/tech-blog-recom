import pytest
from bs4 import BeautifulSoup
from datetime import datetime
from scrapers import KleppmannScraper


@pytest.fixture
def scraper():
    return KleppmannScraper("https://martin.kleppmann.com/")


@pytest.fixture
def index_html():
    return """
    <html>
        <body>
            <li class="archive-item">
                <a href="/2024/01/test-post-1">Post 1</a>
            </li>
            <li class="archive-item">
                <a href="/2024/02/test-post-2">Post 2</a>
            </li>
            <li class="not-archive-item">
                <a href="/about">About</a>
            </li>
        </body>
    </html>
    """


@pytest.fixture
def post_html():
    return """
    <html>
        <body>
            <h1>Test Blog Post Title</h1>
            <div class="date">15 April 2024</div>
            <div class="post">
                <p>This is the first paragraph.</p>
                <p>This is the second paragraph.</p>
            </div>
        </body>
    </html>
    """


def test_extract_blog_links(scraper, index_html):
    soup = BeautifulSoup(index_html, "html.parser")
    links = scraper.extract_blog_links(soup)

    assert len(links) == 2
    assert links[0] == "https://martin.kleppmann.com/2024/01/test-post-1"
    assert links[1] == "https://martin.kleppmann.com/2024/02/test-post-2"


def test_extract_metadata(scraper, post_html):
    soup = BeautifulSoup(post_html, "html.parser")
    metadata = scraper.extract_metadata(soup, "https://martin.kleppmann.com/test-post")

    # Test all metadata fields
    assert metadata["url"] == "https://martin.kleppmann.com/test-post"
    assert metadata["title"] == "Test Blog Post Title"
    assert metadata["author"] == "Martin Kleppmann"  # Author is always Martin Kleppmann
    assert metadata["source_name"] == "Martin Kleppmann"

    # Test date parsing
    assert isinstance(metadata["published_date"], datetime)
    assert metadata["published_date"].year == 2024
    assert metadata["published_date"].month == 4
    assert metadata["published_date"].day == 15

    # Test content extraction
    assert "This is the first paragraph" in metadata["content"]
    assert "This is the second paragraph" in metadata["content"]


def test_extract_metadata_missing_fields(scraper):
    minimal_html = """
    <html>
        <body>
            <h1>Test Title</h1>
            <div class="post">
                <p>Some content</p>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(minimal_html, "html.parser")
    metadata = scraper.extract_metadata(soup, "https://martin.kleppmann.com/test-post")

    # Should handle missing fields gracefully
    assert metadata["title"] == "Test Title"
    assert metadata["author"] == "Martin Kleppmann"  # Author is always set
    assert metadata["published_date"] is None
    assert "Some content" in metadata["content"]
