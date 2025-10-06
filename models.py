import logging
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from blog_app.extensions import db

logger = logging.getLogger(__name__)


# =====================
# WordPress-Style Post Model (Unified)
# =====================

class Post(db.Model):
    """Unified WordPress-style post model for all content types."""

    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)

    # Core content
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(500))
    author = db.Column(db.String(100), nullable=False, default="Admin")

    # WordPress-style fields
    post_type = db.Column(db.String(20), default='post', nullable=False, index=True)
    post_status = db.Column(db.String(20), default='draft', nullable=False, index=True)
    post_parent = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)

    # Post ownership
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user = db.relationship("User", backref=db.backref("posts", lazy=True))

    # Post metadata (kept for convenience, can be moved to PostMeta if needed)
    featured = db.Column(db.Boolean, default=False, nullable=False)

    # Taxonomy relations (for posts that support them)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    category_obj = db.relationship('Category', backref=db.backref('posts', lazy=True))
    tag_items = db.relationship('Tag', secondary='post_tags', backref=db.backref('posts', lazy=True))

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, index=True)

    # Relationships
    children = db.relationship(
        'Post',
        backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic'
    )
    meta_items = db.relationship('PostMeta', backref='post', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Post {self.post_type}:{self.title}>"

    # WordPress-style property aliases
    @property
    def published(self):
        """WordPress 'publish' status check."""
        return self.post_status == 'publish'

    @published.setter
    def published(self, value):
        """Set post_status based on boolean published."""
        self.post_status = 'publish' if value else 'draft'

    def is_owned_by(self, user):
        """Check if the post is owned by the given user."""
        if not user or not user.is_authenticated:
            return False
        return self.user_id == user.id

    def get_meta(self, key, default=None):
        """Get a post meta value by key."""
        meta = PostMeta.query.filter_by(post_id=self.id, meta_key=key).first()
        return meta.meta_value if meta else default

    def set_meta(self, key, value):
        """Set a post meta value."""
        meta = PostMeta.query.filter_by(post_id=self.id, meta_key=key).first()
        if meta:
            meta.meta_value = str(value)
        else:
            meta = PostMeta(post_id=self.id, meta_key=key, meta_value=str(value))
            db.session.add(meta)

    def delete_meta(self, key):
        """Delete a post meta value."""
        PostMeta.query.filter_by(post_id=self.id, meta_key=key).delete()

    def get_all_meta(self):
        """Get all meta as a dictionary."""
        return {meta.meta_key: meta.meta_value for meta in self.meta_items}

    def to_dict(self):
        """Convert post to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "content": self.content,
            "excerpt": self.excerpt,
            "author": self.author,
            "post_type": self.post_type,
            "post_status": self.post_status,
            "post_parent": self.post_parent,
            "published": self.published,
            "featured": self.featured,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }

        # Add taxonomies if this post type supports them
        if self.category_obj:
            result["category"] = self.category_obj.name
        if self.tag_items:
            result["tags"] = [t.name for t in self.tag_items]

        return result


class PostType(db.Model):
    """WordPress-style post type registration."""

    __tablename__ = "post_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False, index=True)  # post, page, project
    label = db.Column(db.String(100), nullable=False)  # Blog Posts, Pages, Projects
    label_singular = db.Column(db.String(100), nullable=False)  # Blog Post, Page, Project
    description = db.Column(db.String(500))

    # Capabilities
    hierarchical = db.Column(db.Boolean, default=False, nullable=False)  # Can have parent/child
    has_archive = db.Column(db.Boolean, default=True, nullable=False)  # Has archive page (/blog/, /projects/)

    # Feature support
    supports_categories = db.Column(db.Boolean, default=False, nullable=False)
    supports_tags = db.Column(db.Boolean, default=False, nullable=False)
    supports_excerpt = db.Column(db.Boolean, default=True, nullable=False)
    supports_featured_image = db.Column(db.Boolean, default=True, nullable=False)

    # Admin UI
    menu_icon = db.Column(db.String(50))  # iconoir class name
    menu_position = db.Column(db.Integer, default=20)
    show_in_menu = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<PostType {self.name}>"

    @staticmethod
    def get_by_name(name):
        """Get post type by name."""
        return PostType.query.filter_by(name=name).first()

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "label": self.label,
            "label_singular": self.label_singular,
            "hierarchical": self.hierarchical,
            "has_archive": self.has_archive,
            "supports_categories": self.supports_categories,
            "supports_tags": self.supports_tags,
            "supports_excerpt": self.supports_excerpt,
            "supports_featured_image": self.supports_featured_image,
        }


class PostMeta(db.Model):
    """WordPress-style post metadata (custom fields)."""

    __tablename__ = "post_meta"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False, index=True)
    meta_key = db.Column(db.String(255), nullable=False, index=True)
    meta_value = db.Column(db.Text)

    # Create compound index for faster lookups
    __table_args__ = (
        db.Index('idx_post_meta_key', 'post_id', 'meta_key'),
    )

    def __repr__(self):
        return f"<PostMeta post_id={self.post_id} {self.meta_key}={self.meta_value}>"


# =====================
# User Model
# =====================

class User(UserMixin, db.Model):
    """Model for authenticated users."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    github_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200))
    avatar_url = db.Column(db.String(500))

    # User metadata
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        """Convert user to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "github_id": self.github_id,
            "username": self.username,
            "email": self.email,
            "avatar_url": self.avatar_url,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


# =====================
# Settings Model
# =====================

class Setting(db.Model):
    """Model for application settings (key-value store)."""

    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(500))

    # Timestamps
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"

    @staticmethod
    def get(key, default=None):
        """Get a setting value by key."""
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value, description=None):
        """Set a setting value."""
        try:
            setting = Setting.query.filter_by(key=key).first()
            if setting:
                setting.value = str(value)
                if description:
                    setting.description = description
            else:
                setting = Setting(key=key, value=str(value), description=description)
                db.session.add(setting)

            try:
                db.session.commit()
                return setting
            except IntegrityError as e:
                db.session.rollback()
                logger.error(f"IntegrityError setting {key}: {str(e)}")
                raise ValueError(f"Setting '{key}' conflicts with existing data")
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"SQLAlchemyError setting {key}: {str(e)}")
                raise ValueError(f"Database error setting '{key}'")
        except Exception as e:
            logger.error(f"Unexpected error setting {key}: {str(e)}")
            raise ValueError(f"Failed to set '{key}'")


# =====================
# Taxonomy Models
# =====================

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=True)

    def __repr__(self):
        return f'<Category {self.name}>'


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=True)

    def __repr__(self):
        return f'<Tag {self.name}>'


# Many-to-many relationship table
post_tags = db.Table(
    'post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
)
