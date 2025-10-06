import logging

from flask import current_app
from flask_migrate import upgrade

from blog_app.extensions import db
from blog_app.utils.database import safe_db_add
from datetime import datetime

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
        from models import Post

        if Post.query.filter_by(post_type='post').first():
            print("Seed skipped: posts already exist")
            return
        post = Post(
            title="Hello World",
            slug="hello-world",
            content="# Hello World\n\nThis is your first post.",
            excerpt="This is your first post.",
            author="Admin",
            post_type='post',  # WordPress-style
            post_status='publish',  # WordPress-style
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

    @app.cli.command("publish-scheduled")
    def publish_scheduled():
        """Publish scheduled posts whose publish time has arrived."""
        from models import Post

        now = datetime.utcnow()
        posts = (
            Post.query
            .filter(Post.post_type == 'post')
            .filter(Post.post_status == 'draft')
            .filter(Post.published_at.isnot(None))
            .filter(Post.published_at <= now)
            .all()
        )
        count = 0
        for p in posts:
            p.post_status = 'publish'  # WordPress-style
            count += 1
        db.session.commit()
        print(f"Published {count} scheduled post(s) at {now.isoformat()} UTC")
