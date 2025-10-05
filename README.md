# Flask Blog

A modern, full-featured blog built with Flask and SQLAlchemy - similar to WordPress but lightweight and customizable.

## Features

### Blog Features
- ✅ **Full CMS functionality** - Create, edit, delete blog posts
- ✅ **Admin dashboard** - Manage all posts from one interface
- ✅ **Rich post metadata** - Categories, tags, excerpts, featured posts
- ✅ **Draft/Publish workflow** - Save drafts and publish when ready
- ✅ **RESTful API** - JSON endpoints for programmatic access
- ✅ **SQLite database** - No external database required
- ✅ **Database migrations** - Easy schema updates with Flask-Migrate

### Frontend Features
- Responsive design with animated background grid
- Smooth scrolling navigation
- Blog listing and individual post pages
- Projects showcase section
- System architecture section
- About me section

## Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies (creates .venv automatically)
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Seed Sample Data

```bash
# Create sample blog posts
flask seed-db
```

### 3. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Using the Blog

### Admin Dashboard

Access the admin dashboard at: `http://localhost:5000/admin`

Here you can:
- View all blog posts (published and drafts)
- Create new posts
- Edit existing posts
- Delete posts
- Toggle published/draft status
- Mark posts as featured

### Creating a New Post

1. Go to `http://localhost:5000/admin`
2. Click "New Post"
3. Fill in the form:
   - **Title**: Your post title
   - **Slug**: URL-friendly identifier (auto-generated from title)
   - **Excerpt**: Short summary (optional)
   - **Content**: Full post content
   - **Author**: Author name
   - **Category**: Select a category
   - **Tags**: Comma-separated tags
   - **Published**: Check to publish immediately
   - **Featured**: Check to feature on homepage
4. Click "Create Post"

### Viewing Blog Posts

- **All posts**: `http://localhost:5000/blog`
- **Single post**: `http://localhost:5000/blog/<slug>`
- **Homepage**: `http://localhost:5000/` (shows featured content)

### API Endpoints

The blog provides RESTful JSON endpoints:

```bash
# Get all published posts
curl http://localhost:5000/api/posts

# Get a specific post
curl http://localhost:5000/api/posts/<slug>

# Get featured posts
curl http://localhost:5000/api/posts/featured
```

## Project Structure

```
blog/
├── app.py                      # Main Flask application with routes
├── models.py                   # Database models (BlogPost)
├── forms.py                    # WTForms for blog post creation/editing
├── config.py                   # Application configuration
├── blog.db                     # SQLite database (created automatically)
├── templates/
│   ├── index.html             # Homepage
│   ├── blog_list.html         # Blog post listing
│   ├── blog_post.html         # Individual blog post
│   └── admin/
│       ├── base.html          # Admin base template
│       ├── dashboard.html     # Admin dashboard
│       └── post_form.html     # Post creation/edit form
├── static/
│   ├── css/
│   │   └── style.css          # Styles
│   └── js/
│       └── main.js            # Client-side JavaScript
├── pyproject.toml             # Project dependencies
└── README.md
```

## CLI Commands

```bash
# Initialize the database
flask init-db

# Seed sample blog posts
flask seed-db

# Run database migrations (if needed)
flask db upgrade
```

## Development

- Flask runs in debug mode by default
- Auto-reload enabled for development
- SQLite database stored in `blog.db`
- All templates in `templates/` directory
- Static files in `static/` directory

## Database Model

The `BlogPost` model includes:

- `id` - Primary key
- `title` - Post title
- `slug` - URL-friendly identifier
- `content` - Full post content
- `excerpt` - Short summary
- `author` - Author name
- `published` - Published status (boolean)
- `featured` - Featured status (boolean)
- `category` - Post category
- `tags` - Comma-separated tags
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp
- `published_at` - Publication timestamp

## Customization

### Styling

Edit `static/css/style.css` to customize:
- Color scheme (CSS variables in `:root`)
- Typography
- Layout and spacing

### Categories

Edit `forms.py` to add/remove categories:

```python
category = SelectField(
    'Category',
    choices=[
        ('technology', 'Technology'),
        ('programming', 'Programming'),
        # Add your categories here
    ],
)
```

### Templates

- `templates/index.html` - Homepage content
- `templates/blog_list.html` - Blog listing page
- `templates/blog_post.html` - Individual post display
- `templates/admin/` - Admin interface templates

## Future Enhancements

- User authentication for admin access
- Rich text editor (TinyMCE/CKEditor)
- Image upload and management
- Search functionality
- Comments system
- RSS feed
- Social media sharing
- SEO optimization (meta tags, sitemaps)
- Multi-user support with roles

## License

MIT License - Feel free to use and modify for your own projects!

- Run migrations:
  - flask --app app.py db upgrade
- Existing DB not under Alembic:
  - flask --app app.py db stamp head, then future changes use migrate/upgrade.