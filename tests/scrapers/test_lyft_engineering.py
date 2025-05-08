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


def test_extract_blog_links(scraper, index_html):
    soup = BeautifulSoup(index_html, "html.parser")
    links = scraper.extract_blog_links(soup)

    assert len(links) == 2
    assert links[0] == "https://eng.lyft.com/2024/01/test-post-1"
    assert links[1] == "https://eng.lyft.com/2024/02/test-post-2"


def test_extract_metadata(scraper, post_html):
    soup = BeautifulSoup(post_html, "html.parser")
    metadata = scraper.extract_metadata(soup, "https://eng.lyft.com/test-post")

    # Test all metadata fields
    assert metadata["url"] == "https://eng.lyft.com/test-post"
    assert metadata["title"] == "Test Blog Post Title"
    assert metadata["author"] == "John Doe"
    assert metadata["source_name"] == "Lyft Engineering"

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
