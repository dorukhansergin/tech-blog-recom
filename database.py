import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import os


class Database:
    def __init__(self, db_path: str = "blog_posts.db"):
        """Initialize database connection.

        Args:
            db_path (str): Path to the SQLite database file. Defaults to "blog_posts.db"
        """
        self.db_path = db_path
        self.conn = None

        try:
            # Create database directory if it doesn't exist
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)

            # Connect to database (creates file if it doesn't exist)
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            self.create_tables()
        except sqlite3.Error as e:
            raise sqlite3.Error(
                f"Failed to open/create database at {db_path}: {str(e)}\n"
                "Please check if you have write permissions in the directory."
            )

    def create_tables(self):
        """Create necessary database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Create posts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT,
                published_date TEXT,
                source_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        self.conn.commit()

    def save_post(self, post_data: Dict[str, Any]) -> bool:
        """Save a blog post to the database."""
        try:
            cursor = self.conn.cursor()

            # Convert datetime to string if present
            published_date = post_data.get("published_date")
            if published_date and isinstance(published_date, datetime):
                published_date = published_date.isoformat()

            cursor.execute(
                """
                INSERT OR REPLACE INTO posts (
                    url, title, content, author, published_date, source_name, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    post_data["url"],
                    post_data["title"],
                    post_data["content"],
                    post_data.get("author"),
                    published_date,
                    post_data["source_name"],
                    datetime.now().isoformat(),
                ),
            )

            self.conn.commit()
            return True

        except Exception as e:
            print(f"Error saving post to database: {str(e)}")
            return False

    def get_posts(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get posts from the database with optional filters."""
        try:
            cursor = self.conn.cursor()

            # Build query
            query = "SELECT * FROM posts WHERE 1=1"
            params = []

            if filters:
                if "source_name" in filters:
                    query += " AND source_name = ?"
                    params.append(filters["source_name"])

                if "author" in filters:
                    query += " AND author = ?"
                    params.append(filters["author"])

                if "date_from" in filters:
                    query += " AND published_date >= ?"
                    params.append(filters["date_from"])

                if "date_to" in filters:
                    query += " AND published_date <= ?"
                    params.append(filters["date_to"])

            # Add order by clause
            query += " ORDER BY published_date DESC"

            # Execute query
            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Convert rows to dictionaries
            posts = []
            for row in rows:
                post = dict(row)
                # Convert string dates back to datetime objects
                if post["published_date"]:
                    try:
                        post["published_date"] = datetime.fromisoformat(
                            post["published_date"]
                        )
                    except:
                        pass
                if post["created_at"]:
                    try:
                        post["created_at"] = datetime.fromisoformat(post["created_at"])
                    except:
                        pass
                posts.append(post)

            return posts

        except Exception as e:
            print(f"Error getting posts from database: {str(e)}")
            return []

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
