import os
import uuid
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session, send_from_directory
from markupsafe import Markup
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from models import db, BlogPost, User, Setting
from forms import BlogPostForm, SettingsForm
from config import config

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the admin panel.'

# Initialize OAuth
oauth = OAuth(app)
github = oauth.register(
    name='github',
    client_id=app.config['GITHUB_CLIENT_ID'],
    client_secret=app.config['GITHUB_CLIENT_SECRET'],
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=app.config['GITHUB_CALLBACK_URL'],
    client_kwargs={'scope': 'user:email'},
)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def render_markdown(text):
    """Convert markdown to HTML with syntax highlighting."""
    md = markdown.Markdown(extensions=[
        FencedCodeExtension(),
        CodeHiliteExtension(css_class='highlight', linenums=False),
        TableExtension(),
        'nl2br',  # Convert newlines to <br>
        'sane_lists',  # Better list handling
    ])
    return md.convert(text)


def process_image(image_path, max_width=None, max_height=None, quality=None):
    """Process an image: resize, optimize, and convert to RGB if needed."""
    if max_width is None:
        max_width = int(Setting.get('image_max_width', app.config['IMAGE_MAX_WIDTH']))
    if max_height is None:
        max_height = int(Setting.get('image_max_height', app.config['IMAGE_MAX_HEIGHT']))
    if quality is None:
        quality = int(Setting.get('image_quality', app.config['IMAGE_QUALITY']))

    # Open the image
    img = Image.open(image_path)

    # Convert to RGB if necessary (for PNG with transparency, etc.)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Create a white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Resize if image is larger than max dimensions
    if img.width > max_width or img.height > max_height:
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    # Save optimized image
    img.save(image_path, 'JPEG', quality=quality, optimize=True)

    return img


# Create tables and upload folder
with app.app_context():
    db.create_all()
    app.config['UPLOAD_FOLDER'].mkdir(parents=True, exist_ok=True)


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/login')
def login():
    """Render login page."""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    return render_template('login.html')


@app.route('/auth/github')
def github_login():
    """Redirect to GitHub for OAuth authentication."""
    redirect_uri = url_for('github_callback', _external=True)
    return github.authorize_redirect(redirect_uri)


@app.route('/auth/github/callback')
def github_callback():
    """Handle GitHub OAuth callback."""
    try:
        token = github.authorize_access_token()
        resp = github.get('https://api.github.com/user', token=token)
        profile = resp.json()

        # Get user's email
        email_resp = github.get('https://api.github.com/user/emails', token=token)
        emails = email_resp.json()
        primary_email = next((email['email'] for email in emails if email['primary']), None)

        github_id = str(profile['id'])
        username = profile['login']

        # Find or create user
        user = User.query.filter_by(github_id=github_id).first()

        if not user:
            # Create new user
            user = User(
                github_id=github_id,
                username=username,
                email=primary_email,
                avatar_url=profile.get('avatar_url'),
            )

            # Check if user should be admin
            if app.config['ADMIN_GITHUB_USERNAME'] and username == app.config['ADMIN_GITHUB_USERNAME']:
                user.is_admin = True

            db.session.add(user)
            db.session.commit()
            flash(f'Welcome {username}! Your account has been created.', 'success')
        else:
            # Update existing user
            user.username = username
            user.email = primary_email
            user.avatar_url = profile.get('avatar_url')
            user.last_login = datetime.utcnow()
            db.session.commit()

        # Log in user
        login_user(user)
        flash(f'Successfully logged in as {username}!', 'success')

        # Redirect to next page or admin dashboard
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))

    except Exception as e:
        flash(f'Authentication failed: {str(e)}', 'error')
        return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


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
    # Render markdown to HTML
    post_html = render_markdown(post.content)
    return render_template('blog_post.html', post=post, post_html=post_html)


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard showing all posts."""
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template('admin/dashboard.html', posts=posts)


@app.route('/admin/posts/new', methods=['GET', 'POST'])
@login_required
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
            user_id=current_user.id,  # Assign current user as owner
        )

        if form.published.data:
            post.published_at = datetime.utcnow()

        db.session.add(post)
        db.session.commit()

        if form.published.data:
            view_url = url_for('blog_post', slug=post.slug)
            flash(Markup(f'Post created successfully! <a href="{view_url}" target="_blank" style="color: #155724; text-decoration: underline; font-weight: 600;">View Post →</a>'), 'success')
        else:
            flash('Post created successfully as draft!', 'success')
        return redirect(url_for('admin_dashboard'))

    # Set default author
    form.author.data = 'Admin'

    return render_template('admin/post_form.html', form=form, title='New Post')


@app.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
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

        if form.published.data:
            view_url = url_for('blog_post', slug=post.slug)
            flash(Markup(f'Post updated successfully! <a href="{view_url}" target="_blank" style="color: #155724; text-decoration: underline; font-weight: 600;">View Post →</a>'), 'success')
        else:
            flash('Post updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/post_form.html', form=form, title='Edit Post', post=post)


@app.route('/admin/posts/<int:post_id>/preview')
@login_required
def admin_preview_post(post_id):
    """Preview a blog post (published or draft)."""
    post = BlogPost.query.get_or_404(post_id)
    # Render markdown to HTML
    post_html = render_markdown(post.content)
    return render_template('blog_post.html', post=post, post_html=post_html, is_preview=True)


@app.route('/admin/posts/<int:post_id>/publish', methods=['POST'])
@login_required
def admin_publish_post(post_id):
    """Publish a draft post."""
    post = BlogPost.query.get_or_404(post_id)

    # Check ownership
    if not post.is_owned_by(current_user):
        flash('You do not have permission to publish this post.', 'error')
        return redirect(url_for('admin_dashboard'))

    # Publish the post
    post.published = True
    post.published_at = datetime.utcnow()
    db.session.commit()

    flash(Markup(f'Post published successfully! <a href="{url_for("blog_post", slug=post.slug)}" target="_blank" style="color: #155724; text-decoration: underline; font-weight: 600;">View Post →</a>'), 'success')
    return redirect(url_for('blog_post', slug=post.slug))


@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    """Delete a blog post."""
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()

    flash('Post deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    """Admin settings page."""
    form = SettingsForm()

    if form.validate_on_submit():
        # Save image processing settings
        Setting.set('image_max_width', form.image_max_width.data, 'Maximum width for uploaded images')
        Setting.set('image_max_height', form.image_max_height.data, 'Maximum height for uploaded images')
        Setting.set('image_quality', form.image_quality.data, 'JPEG quality (1-100)')

        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))

    # Load current settings or use defaults
    form.image_max_width.data = int(Setting.get('image_max_width', app.config['IMAGE_MAX_WIDTH']))
    form.image_max_height.data = int(Setting.get('image_max_height', app.config['IMAGE_MAX_HEIGHT']))
    form.image_quality.data = int(Setting.get('image_quality', app.config['IMAGE_QUALITY']))

    return render_template('admin/settings.html', form=form)


@app.route('/admin/upload-image', methods=['POST'])
@login_required
def upload_image():
    """Handle image uploads from Toast UI Editor."""
    if 'image' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        # Generate unique filename (always .jpg as we convert to JPEG)
        filename = f"{uuid.uuid4().hex}.jpg"

        # Save file temporarily
        filepath = app.config['UPLOAD_FOLDER'] / filename
        file.save(filepath)

        # Process image (resize, optimize, convert to JPEG)
        try:
            process_image(filepath)
        except Exception as e:
            # If processing fails, remove the file and return error
            filepath.unlink(missing_ok=True)
            return jsonify({'error': f'Image processing failed: {str(e)}'}), 400

        # Return URL for Toast UI Editor
        url = url_for('static', filename=f'uploads/{filename}')
        return jsonify({'url': url})

    return jsonify({'error': 'Invalid file type'}), 400


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
