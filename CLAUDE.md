# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A modern Flask-based personal blog application with a futuristic design featuring:
- Responsive navigation with smooth scrolling
- Hero section with call-to-action
- Projects showcase section
- System architecture section
- Playbooks section
- About me section

## Development Setup

### Quick Start with uv (recommended)

```bash
# Sync all dependencies (creates .venv automatically)
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run development server
python app.py
```

Application will be available at `http://localhost:5000`

### Alternative: Manual Setup

```bash
# Create virtual environment
uv venv

# Activate it
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install flask python-dotenv

# Run server
python app.py
```

### Running the Application

```bash
# After activating .venv
python app.py

# Or use Flask CLI
flask run
```

## Project Structure

```
blog/
├── app.py                  # Main Flask application with routes
├── templates/
│   └── index.html         # Jinja2 template for main page
├── static/
│   ├── css/
│   │   └── style.css      # Extracted styles with CSS custom properties
│   └── js/
│       └── main.js        # Client-side JavaScript
├── template.html          # Original HTML template (legacy)
├── pyproject.toml         # Project metadata and dependencies
├── CLAUDE.md              # This file
└── README.md              # User-facing documentation
```

## Architecture

### Backend (Flask)
- Simple Flask application in `app.py`
- Single route (`/`) renders the index template
- Debug mode enabled for development
- Runs on `0.0.0.0:5000` by default

### Frontend
- **Templates**: Jinja2 templates in `templates/`
- **Static files**: Organized in `static/css/` and `static/js/`
- **CSS**: Uses CSS custom properties (variables) for theming
- **JavaScript**: Vanilla JS with Intersection Observer API for animations

### Design System
- **Color scheme**: Warm neutral palette (beige/brown tones defined in CSS `:root`)
- **Typography**: Inter font family from Google Fonts
- **Components**: Cards, navigation, hero, footer sections
- **Animations**: Grid background, fade-in effects, smooth scrolling
- **Responsive**: Mobile-friendly with breakpoint at 768px

## Development Commands

```bash
# Run in development mode (auto-reload enabled)
python app.py

# Install dev dependencies
uv pip install pytest pytest-flask black ruff

# Format code
black app.py

# Lint code
ruff check .
```

## Future Enhancements

- Add database models (Flask-SQLAlchemy)
- Implement admin interface for content management
- Create separate routes for projects, playbooks, about pages
- Add blog post functionality with CRUD operations
- Implement user authentication
- Add testing suite
