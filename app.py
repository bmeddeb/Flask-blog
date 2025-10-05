import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_migrate import Migrate
from models import db, BlogPost
from forms import BlogPostForm
from config import config

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)


# Create tables
with app.app_context():
    db.create_all()


# ============================================================================
# FRONTEND ROUTES
# ============================================================================

@app.route('/')
def index():
    """Render the main blog page."""
    return render_template('index.html')


@app.route('/blog')
def blog_list():
    """Display all published blog posts."""
    posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.published_at.desc()).all()
    return render_template('blog_list.html', posts=posts)


@app.route('/blog/<slug>')
def blog_post(slug):
    """Display a single blog post."""
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    return render_template('blog_post.html', post=post)


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard showing all posts."""
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/dashboard.html', posts=posts)


@app.route('/admin/posts/new', methods=['GET', 'POST'])
def admin_new_post():
    """Create a new blog post."""
    form = BlogPostForm()

    if form.validate_on_submit():
        post = BlogPost(
            title=form.title.data,
            slug=form.slug.data,
            content=form.content.data,
            excerpt=form.excerpt.data,
            author=form.author.data,
            category=form.category.data,
            tags=form.tags.data,
            published=form.published.data,
            featured=form.featured.data,
        )

        if form.published.data:
            post.published_at = datetime.utcnow()

        db.session.add(post)
        db.session.commit()

        flash('Post created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    # Set default author
    form.author.data = 'Admin'

    return render_template('admin/post_form.html', form=form, title='New Post')


@app.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
def admin_edit_post(post_id):
    """Edit an existing blog post."""
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm(obj=post)

    if form.validate_on_submit():
        post.title = form.title.data
        post.slug = form.slug.data
        post.content = form.content.data
        post.excerpt = form.excerpt.data
        post.author = form.author.data
        post.category = form.category.data
        post.tags = form.tags.data

        # Handle publishing
        was_published = post.published
        post.published = form.published.data

        if form.published.data and not was_published:
            post.published_at = datetime.utcnow()

        post.featured = form.featured.data

        db.session.commit()

        flash('Post updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/post_form.html', form=form, title='Edit Post', post=post)


@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
def admin_delete_post(post_id):
    """Delete a blog post."""
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/posts')
def api_posts():
    """Get all published posts as JSON."""
    published_only = request.args.get('published', 'true').lower() == 'true'

    if published_only:
        posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.published_at.desc()).all()
    else:
        posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()

    return jsonify([post.to_dict() for post in posts])


@app.route('/api/posts/<slug>')
def api_post(slug):
    """Get a single post by slug as JSON."""
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    return jsonify(post.to_dict())


@app.route('/api/posts/featured')
def api_featured_posts():
    """Get featured posts as JSON."""
    posts = BlogPost.query.filter_by(published=True, featured=True)\
        .order_by(BlogPost.published_at.desc()).limit(3).all()
    return jsonify([post.to_dict() for post in posts])


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return render_template('500.html'), 500


# ============================================================================
# CLI COMMANDS
# ============================================================================

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized!')


@app.cli.command()
def seed_db():
    """Seed the database with sample posts."""
    sample_posts = [
        BlogPost(
            title='Welcome to My Blog',
            slug='welcome-to-my-blog',
            content='This is my first blog post. I\'m excited to share my thoughts and experiences with you!',
            excerpt='My first blog post welcoming you to this space.',
            author='Admin',
            category='personal',
            tags='welcome,introduction',
            published=True,
            featured=True,
            published_at=datetime.utcnow()
        ),
        BlogPost(
            title='Getting Started with Flask',
            slug='getting-started-with-flask',
            content='Flask is a lightweight WSGI web application framework. It is designed to make getting started quick and easy...',
            excerpt='A beginner\'s guide to Flask web framework.',
            author='Admin',
            category='tutorial',
            tags='python,flask,web-development',
            published=True,
            published_at=datetime.utcnow()
        ),
    ]

    for post in sample_posts:
        db.session.add(post)

    db.session.commit()
    print(f'Seeded {len(sample_posts)} sample posts!')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
