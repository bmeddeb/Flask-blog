from flask import Blueprint, render_template
from blog_app.utils.markdown import render_markdown
from models import BlogPost, Page

bp = Blueprint("public", __name__)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/blog")
def blog_list():
    posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.published_at.desc()).all()
    return render_template("blog_list.html", posts=posts)


@bp.route("/blog/<slug>")
def blog_post(slug):
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    post_html = render_markdown(post.content)
    return render_template("blog_post.html", post=post, post_html=post_html)


@bp.route("/page/<slug>")
def view_page(slug):
    page = Page.query.filter_by(slug=slug, published=True).first_or_404()

    if page.content_type == "markdown":
        content_html = render_markdown(page.content)
        sidebar_html = render_markdown(page.sidebar_content) if page.sidebar_content else None
    else:
        content_html = page.content
        sidebar_html = page.sidebar_content

    if page.layout == "blank":
        return content_html

    return render_template(
        f"pages/layout_{page.layout}.html",
        page=page,
        content_html=content_html,
        sidebar_html=sidebar_html,
    )
