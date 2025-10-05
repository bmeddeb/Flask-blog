import logging

from flask import current_app
from flask_migrate import upgrade

from blog_app.extensions import db
from blog_app.utils.database import safe_db_add

logger = logging.getLogger(__name__)


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Initialize the database by running migrations (preferred)."""
        upgrade()
        print("Database initialized via migrations!")

    @app.cli.command("seed-db")
    def seed_db():
        """Seed the database with sample posts."""
        from datetime import datetime

        from models import BlogPost

        if BlogPost.query.first():
            print("Seed skipped: posts already exist")
            return
        post = BlogPost(
            title="Hello World",
            slug="hello-world",
            content="# Hello World\n\nThis is your first post.",
            excerpt="This is your first post.",
            author="Admin",
            published=True,
            published_at=datetime.utcnow(),
        )
        try:
            success, error = safe_db_add(post, "Sample post created", "Failed to create sample post")
            if success:
                print("Seeded 1 sample post")
            else:
                print(f"Failed to seed database: {error}")
        except Exception as e:
            logger.error(f"Error seeding database: {str(e)}")
            print(f"Failed to seed database: {str(e)}")
