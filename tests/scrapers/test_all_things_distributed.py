import pytest
from bs4 import BeautifulSoup
from datetime import datetime
from scrapers import AllThingsDistributedScraper


@pytest.fixture
def scraper():
    return AllThingsDistributedScraper(
        "https://www.allthingsdistributed.com/articles.html"
    )


@pytest.fixture
def index_html():
    return """
    <html>
        <body>
            <div itemprop="blogPost">
                <a href="/2024/01/test-post-1">Post 1</a>
            </div>
            <div itemprop="blogPost">
                <a href="/2024/02/test-post-2">Post 2</a>
            </div>
            <div class="not-a-blog-post">
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
            <time>April 09, 2024</time>
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
    assert links[0] == "https://www.allthingsdistributed.com/2024/01/test-post-1"
    assert links[1] == "https://www.allthingsdistributed.com/2024/02/test-post-2"


def test_extract_metadata(scraper, post_html):
    soup = BeautifulSoup(post_html, "html.parser")
    metadata = scraper.extract_metadata(
        soup, "https://www.allthingsdistributed.com/test-post"
    )

    # Test all metadata fields
    assert metadata["url"] == "https://www.allthingsdistributed.com/test-post"
    assert metadata["title"] == "Test Blog Post Title"
    assert metadata["author"] == "Werner Vogels"  # Author is always Werner Vogels
    assert metadata["source_name"] == "AllThingsDistributed"

    # Test date parsing
    assert isinstance(metadata["published_date"], datetime)
    assert metadata["published_date"].year == 2024
    assert metadata["published_date"].month == 4
    assert metadata["published_date"].day == 9

    # Test content extraction
    assert "This is the first paragraph" in metadata["content"]
    assert "This is the second paragraph" in metadata["content"]


def test_extract_metadata_missing_fields(scraper):
    minimal_html = """
    <html>
        <body>
            <h1>Test Title</h1>
            <div class="post-content">
                <p>Some content</p>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(minimal_html, "html.parser")
    metadata = scraper.extract_metadata(
        soup, "https://www.allthingsdistributed.com/test-post"
    )

    # Should handle missing fields gracefully
    assert metadata["title"] == "Test Title"
    assert metadata["author"] == "Werner Vogels"  # Author is always set
    assert metadata["published_date"] is None
    assert "Some content" in metadata["content"]


def test_extract_metadata_og_title(scraper):
    html = """
    <html>
        <head>
            <meta property="og:title" content="OG Title Test">
        </head>
        <body>
            <div class="post-content">
                <p>Some content</p>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    metadata = scraper.extract_metadata(
        soup, "https://www.allthingsdistributed.com/test-post"
    )
    assert metadata["title"] == "OG Title Test"


def test_extract_metadata_itemprop_title(scraper):
    html = """
    <html>
        <head>
            <meta itemprop="name" content="Schema.org Title Test">
        </head>
        <body>
            <div class="post-content">
                <p>Some content</p>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    metadata = scraper.extract_metadata(
        soup, "https://www.allthingsdistributed.com/test-post"
    )
    assert metadata["title"] == "Schema.org Title Test"


def test_extract_metadata_json_ld_title(scraper):
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "headline": "JSON-LD Title Test"
            }
            </script>
        </head>
        <body>
            <div class="post-content">
                <p>Some content</p>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    metadata = scraper.extract_metadata(
        soup, "https://www.allthingsdistributed.com/test-post"
    )
    assert metadata["title"] == "JSON-LD Title Test"


def test_extract_metadata_title_tag(scraper):
    html = """
    <html>
        <head>
            <title>Title Tag Test | All Things Distributed</title>
        </head>
        <body>
            <div class="post-content">
                <p>Some content</p>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    metadata = scraper.extract_metadata(
        soup, "https://www.allthingsdistributed.com/test-post"
    )
    assert metadata["title"] == "Title Tag Test"


def test_extract_metadata_title_priority(scraper):
    """Test that title extraction follows the correct priority order."""
    html = """
    <html>
        <head>
            <meta property="og:title" content="OG Title">
            <meta itemprop="name" content="Schema.org Title">
            <script type="application/ld+json">
            {
                "headline": "JSON-LD Title"
            }
            </script>
            <title>Title Tag | All Things Distributed</title>
        </head>
        <body>
            <h1>H1 Title</h1>
            <div class="post-content">
                <p>Some content</p>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    metadata = scraper.extract_metadata(
        soup, "https://www.allthingsdistributed.com/test-post"
    )
    # Should use og:title as it has highest priority
    assert metadata["title"] == "OG Title"
