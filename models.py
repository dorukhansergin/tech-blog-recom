from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

Base = declarative_base()


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author = Column(String(100))
    published_date = Column(DateTime)
    source_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BlogPost(title='{self.title}', source_name='{self.source_name}')>"


@dataclass
class BlogEntry:
    """Raw blog entry before processing."""

    title: str
    url: str
    source: str
    published_at: datetime
    content: str


@dataclass
class ProcessedBlogEntry(BlogEntry):
    """Blog entry after processing with embeddings and keywords."""

    embedding: np.ndarray
    keywords: List[str]
