from flask import current_app
from blog_app.extensions import db


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Initialize the database (via migrations recommended)."""
        # Prefer `flask db upgrade`; this is a fallback initializer.
        db.create_all()
        print("Database initialized!")

    @app.cli.command("seed-db")
    def seed_db():
        """Seed the database with sample posts."""
        from models import BlogPost
        from datetime import datetime

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
        db.session.add(post)
        db.session.commit()
        print("Seeded 1 sample post")
