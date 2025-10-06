"""
Create a sample project to demonstrate WordPress-style architecture.
"""
from datetime import datetime

from blog_app import create_app
from blog_app.extensions import db
from models import Post

app = create_app()

with app.app_context():
    # Check if project already exists
    existing = Post.query.filter_by(slug='flask-blog-cms', post_type='project').first()
    if existing:
        print("✓ Sample project already exists")
        exit(0)

    # Create a sample project
    project = Post(
        title="Flask Blog CMS",
        slug="flask-blog-cms",
        post_type='project',  # WordPress-style: specify type
        post_status='publish',  # WordPress-style: publish status
        content="""# Flask Blog CMS

A modern, WordPress-inspired content management system built with Flask.

## Overview

This project is a full-featured blog platform that demonstrates WordPress-style architecture in Flask. It uses a unified Post model for all content types (posts, pages, projects) with flexible custom fields via PostMeta.

## Key Features

### WordPress-Style Architecture
- **Unified Post Model** - One model for all content types
- **Custom Post Types** - Blog posts, pages, projects, and more
- **Custom Fields** - Flexible metadata via PostMeta
- **Hierarchical Content** - Parent-child relationships for pages

### Content Management
- **Rich Text Editor** - Toast UI Editor with Markdown support
- **Image Upload** - Drag-and-drop with automatic resizing
- **Draft/Publish Workflow** - Schedule posts for future publication
- **Categories & Tags** - Organize content with taxonomies

### Modern UI
- **Admin Dashboard** - WordPress-style admin panel
- **Responsive Design** - Mobile-friendly layouts
- **Dark Code Blocks** - Prism.js syntax highlighting
- **Smooth Animations** - Intersection Observer effects

## Technical Stack

The project uses modern Python and web technologies:
- **Backend**: Flask, SQLAlchemy, Flask-Migrate
- **Database**: SQLite (PostgreSQL-ready)
- **Frontend**: Vanilla JS, CSS Grid, Flexbox
- **Editor**: Toast UI Editor
- **Auth**: GitHub OAuth via Authlib

## Architecture Highlights

### Database Schema
```python
Post (unified model)
├── post_type: 'post', 'page', 'project'
├── post_status: 'publish', 'draft', 'private'
├── post_parent: For hierarchical content
└── relationships: categories, tags, meta

PostType (register content types)
PostMeta (custom fields)
```

### Query Examples
```python
# Get blog posts
posts = Post.query.filter_by(
    post_type='post',
    post_status='publish'
).all()

# Get projects
projects = Post.query.filter_by(
    post_type='project',
    post_status='publish'
).all()

# Custom fields
project.set_meta('github_url', 'https://...')
github = project.get_meta('github_url')
```

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/flask-blog.git
cd flask-blog

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate

# Run migrations
flask db upgrade

# Seed sample data
flask seed-db

# Run server
python app.py
```

## Future Enhancements

- [ ] RESTful API with authentication
- [ ] Full-text search with PostgreSQL
- [ ] Comment system
- [ ] RSS feed generation
- [ ] SEO optimization
- [ ] Multi-user support with roles

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project as a template for your own blog!
""",
        excerpt="A WordPress-inspired CMS built with Flask featuring unified post types, custom fields, and a modern admin interface.",
        author="Admin",
        featured=True,
        created_at=datetime.utcnow(),
        published_at=datetime.utcnow(),
    )

    db.session.add(project)
    db.session.flush()  # Get the ID

    # Add custom fields using PostMeta
    project.set_meta('github_url', 'https://github.com/yourusername/flask-blog')
    project.set_meta('demo_url', 'https://flask-blog-demo.com')
    project.set_meta('tech_stack', 'Python, Flask, SQLAlchemy, SQLite, Jinja2, JavaScript')
    project.set_meta('status', 'active')
    project.set_meta('year', '2025')

    db.session.commit()

    print("✅ Sample project created successfully!")
    print(f"   Title: {project.title}")
    print(f"   Slug: {project.slug}")
    print(f"   Type: {project.post_type}")
    print(f"   Status: {project.post_status}")
    print("\n📋 Custom Fields:")
    for key, value in project.get_all_meta().items():
        print(f"   {key}: {value}")
    print("\n🌐 View at: http://localhost:5000/projects")
    print(f"🔗 Direct link: http://localhost:5000/projects/{project.slug}")
