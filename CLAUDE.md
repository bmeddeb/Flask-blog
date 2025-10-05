# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-featured blog platform built with Flask and SQLAlchemy, similar to WordPress but lightweight and customizable. Features:
- Complete CMS with admin dashboard
- Blog post creation, editing, and deletion
- Draft/publish workflow with featured posts
- RESTful API endpoints
- Responsive frontend with modern design
- SQLite database with automatic migrations

## Development Setup

### Quick Start

```bash
# Install all dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Seed sample data
flask seed-db

# Run development server
python app.py
```

Application runs at `http://localhost:5000`

## Project Structure

```
blog/
├── app.py                      # Main Flask app with all routes
├── models.py                   # SQLAlchemy models (BlogPost)
├── forms.py                    # WTForms for post creation/editing
├── config.py                   # Configuration (dev/prod)
├── blog.db                     # SQLite database (auto-created)
├── templates/
│   ├── index.html             # Homepage
│   ├── blog_list.html         # Blog listing page
│   ├── blog_post.html         # Individual post view
│   └── admin/
│       ├── base.html          # Admin base template
│       ├── dashboard.html     # Posts management
│       └── post_form.html     # Create/edit form
├── static/
│   ├── css/style.css          # Main styles + admin styles
│   └── js/main.js             # Client-side JavaScript
└── migrations/                 # Database migrations (if using flask-migrate)
```

## Architecture

### Backend (Flask + SQLAlchemy)

**Routes:**
- `/` - Homepage (static content)
- `/blog` - List all published posts
- `/blog/<slug>` - View single post
- `/admin` - Admin dashboard (list all posts)
- `/admin/posts/new` - Create new post
- `/admin/posts/<id>/edit` - Edit post
- `/admin/posts/<id>/delete` - Delete post (POST)

**API Routes:**
- `/api/posts` - GET all published posts as JSON
- `/api/posts/<slug>` - GET single post as JSON
- `/api/posts/featured` - GET featured posts as JSON

**Models:**
- `BlogPost` - Main blog post model with fields:
  - id, title, slug, content, excerpt
  - author, published, featured, category, tags
  - created_at, updated_at, published_at

**Forms:**
- `BlogPostForm` - WTForms for creating/editing posts
  - Auto-generates slug from title (JavaScript)
  - Categories: technology, programming, tutorial, news, personal
  - Tags as comma-separated string

**Configuration:**
- `Config` - Base configuration class
- `DevelopmentConfig` - Debug enabled
- `ProductionConfig` - Debug disabled
- Database: SQLite at `blog.db`
- Secret key for CSRF protection

### Frontend

**Templates:**
- Jinja2 templates with template inheritance
- Admin uses `admin/base.html` as base
- Public pages have consistent navigation
- Flash messages for user feedback

**Styling:**
- CSS custom properties for theming
- Admin-specific styles in `admin/base.html`
- Responsive design (768px breakpoint)
- Animations and smooth transitions

**JavaScript:**
- Smooth scrolling navigation
- Intersection Observer for card animations
- Auto-generate slug from title in admin forms
- Navbar background change on scroll

### Database

**BlogPost Model Fields:**
```python
id              # Integer, primary key
title           # String(200), required
slug            # String(200), unique, required
content         # Text, required
excerpt         # String(500), optional
author          # String(100), default='Admin'
published       # Boolean, default=False
featured        # Boolean, default=False
category        # String(50), optional
tags            # String(200), comma-separated
created_at      # DateTime, auto-set
updated_at      # DateTime, auto-update
published_at    # DateTime, set when published
```

## Development Commands

```bash
# Database commands
flask init-db              # Initialize database
flask seed-db              # Create sample posts
flask db upgrade           # Run migrations

# Development
python app.py              # Run with debug mode
flask run                  # Alternative run command

# Code quality
black app.py models.py forms.py    # Format code
ruff check .                        # Lint code
```

## Common Development Tasks

### Adding a New Category

Edit `forms.py`:
```python
category = SelectField(
    'Category',
    choices=[
        # Add new category here
        ('mycategory', 'My Category'),
    ],
)
```

### Customizing Colors

Edit `static/css/style.css` `:root` section:
```css
:root {
    --primary-bg: #FDFBF7;
    --accent-color: #8B7355;
    /* Modify colors here */
}
```

### Adding New Fields to BlogPost

1. Update `models.py` - add field to BlogPost model
2. Update `forms.py` - add field to BlogPostForm
3. Update `templates/admin/post_form.html` - add form input
4. Update `app.py` - handle field in create/edit routes
5. Run migration: `flask db migrate -m "Add field"`

### Creating Custom Routes

Add to `app.py`:
```python
@app.route('/my-route')
def my_view():
    # Your logic here
    return render_template('my_template.html')
```

## Testing the Application

### Manual Testing Checklist

1. **Admin Dashboard**
   - Visit `/admin` - should show all posts
   - Click "New Post" - should show form
   - Create post - should save and redirect
   - Edit post - should update correctly
   - Delete post - should remove from database

2. **Blog Frontend**
   - Visit `/blog` - should list published posts
   - Click post - should show full content
   - Check categories and tags display
   - Verify draft posts don't appear

3. **API Endpoints**
   - `curl localhost:5000/api/posts` - should return JSON
   - Verify only published posts returned
   - Check featured posts endpoint

### Database Operations

```bash
# Backup database
cp blog.db blog.db.backup

# Reset database
rm blog.db
python app.py  # Auto-creates new database
flask seed-db   # Add sample data

# Check database contents
sqlite3 blog.db "SELECT title, published FROM blog_posts;"
```

## Security Considerations

- CSRF protection enabled via Flask-WTF
- No authentication currently (admin is public)
- Secret key set in config (change for production)
- Input validation via WTForms
- SQL injection protected by SQLAlchemy ORM

## Future Enhancements (Roadmap)

High Priority:
- User authentication (Flask-Login)
- Rich text editor (TinyMCE/CKEditor)
- Image upload and management

Medium Priority:
- Search functionality
- Comments system
- RSS feed generation
- SEO meta tags

Low Priority:
- Multi-user support with roles
- Analytics dashboard
- Social media sharing buttons
- Export/import functionality

## Troubleshooting

### Database locked error
- Stop all running Flask instances
- Close database connections
- Restart the application

### Changes not appearing
- Clear browser cache
- Check if debug mode is enabled
- Verify auto-reload is working

### Form validation errors
- Check CSRF token is included
- Verify all required fields filled
- Check field length constraints

### Port already in use
- Kill existing process: `lsof -ti:5000 | xargs kill`
- Or use different port in app.py
