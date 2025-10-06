from flask import Blueprint, render_template
from blog_app.utils.markdown import render_markdown
from models import Post

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/blog")
def blog_list():
    # WordPress-style: filter by post_type and post_status
    posts = Post.query.filter_by(
        post_type='post',
        post_status='publish'
    ).order_by(Post.published_at.desc()).all()
    return render_template("blog_list.html", posts=posts)


@bp.route("/blog/<slug>")
def blog_post(slug):
    # WordPress-style: any published post type
    post = Post.query.filter_by(slug=slug, post_status='publish').first_or_404()
    post_html = render_markdown(post.content)
    return render_template("blog_post.html", post=post, post_html=post_html)


@bp.route("/page/<slug>")
def view_page(slug):
    # WordPress-style: pages are posts with post_type='page'
    page = Post.query.filter_by(
        slug=slug,
        post_type='page',
        post_status='publish'
    ).first_or_404()

    # Get page metadata from PostMeta
    content_type = page.get_meta('content_type', 'markdown')
    layout = page.get_meta('layout', 'full-width')
    sidebar_content = page.get_meta('sidebar_content', '')

    if content_type == "markdown":
        content_html = render_markdown(page.content)
        sidebar_html = render_markdown(sidebar_content) if sidebar_content else None
    else:
        content_html = page.content
        sidebar_html = sidebar_content

    if layout == "blank":
        return content_html

    return render_template(
        f"pages/layout_{layout}.html",
        page=page,
        content_html=content_html,
        sidebar_html=sidebar_html,
    )


@bp.route("/projects")
def projects_list():
    """WordPress-style: Projects listing page."""
    projects = Post.query.filter_by(
        post_type='project',
        post_status='publish'
    ).order_by(Post.created_at.desc()).all()
    return render_template("projects.html", projects=projects)


@bp.route("/projects/<slug>")
def project_detail(slug):
    """WordPress-style: Single project view."""
    project = Post.query.filter_by(
        slug=slug,
        post_type='project',
        post_status='publish'
    ).first_or_404()
    project_html = render_markdown(project.content)
    return render_template("project.html", project=project, project_html=project_html)
