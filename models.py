from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class BlogPost(db.Model):
    """Model for blog posts."""

    __tablename__ = 'blog_posts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(500))
    author = db.Column(db.String(100), nullable=False, default='Admin')

    # Post ownership
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('posts', lazy=True))

    # Post metadata
    published = db.Column(db.Boolean, default=False, nullable=False)
    featured = db.Column(db.Boolean, default=False, nullable=False)
    category = db.Column(db.String(50))
    tags = db.Column(db.String(200))  # Comma-separated tags

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<BlogPost {self.title}>'

    def is_owned_by(self, user):
        """Check if the post is owned by the given user."""
        if not user or not user.is_authenticated:
            return False
        return self.user_id == user.id

    def to_dict(self):
        """Convert blog post to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'excerpt': self.excerpt,
            'author': self.author,
            'published': self.published,
            'featured': self.featured,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }


class User(UserMixin, db.Model):
    """Model for authenticated users."""

    __tablename__ = 'users'

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
        return f'<User {self.username}>'

    def to_dict(self):
        """Convert user to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'github_id': self.github_id,
            'username': self.username,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }


class Setting(db.Model):
    """Model for application settings (key-value store)."""

    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(500))

    # Timestamps
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'

    @staticmethod
    def get(key, default=None):
        """Get a setting value by key."""
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value, description=None):
        """Set a setting value."""
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
            if description:
                setting.description = description
        else:
            setting = Setting(key=key, value=str(value), description=description)
            db.session.add(setting)
        db.session.commit()
        return setting


class Page(db.Model):
    """Model for static pages with customizable layouts."""

    __tablename__ = 'pages'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    sidebar_content = db.Column(db.Text)  # Content for sidebar layouts

    # Layout options: 'full-width', 'sidebar-left', 'sidebar-right', 'blank'
    layout = db.Column(db.String(50), nullable=False, default='full-width')

    # Content type: 'markdown' or 'html'
    content_type = db.Column(db.String(20), nullable=False, default='markdown')

    # Page ownership
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('pages', lazy=True))

    # Page metadata
    published = db.Column(db.Boolean, default=False, nullable=False)
    show_in_nav = db.Column(db.Boolean, default=False, nullable=False)  # Show in navigation menu
    nav_order = db.Column(db.Integer, default=0)  # Order in navigation

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<Page {self.title}>'

    def is_owned_by(self, user):
        """Check if the page is owned by the given user."""
        if not user or not user.is_authenticated:
            return False
        return self.user_id == user.id

    def to_dict(self):
        """Convert page to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'content': self.content,
            'sidebar_content': self.sidebar_content,
            'layout': self.layout,
            'content_type': self.content_type,
            'published': self.published,
            'show_in_nav': self.show_in_nav,
            'nav_order': self.nav_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }
