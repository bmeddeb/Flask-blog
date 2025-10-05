from flask import Blueprint, jsonify, request
from models import BlogPost

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/posts")
def api_posts():
    published_only = request.args.get("published", "true").lower() == "true"
    if published_only:
        posts = (
            BlogPost.query.filter_by(published=True).order_by(BlogPost.published_at.desc()).all()
        )
    else:
        posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return jsonify([post.to_dict() for post in posts])


@bp.get("/posts/<slug>")
def api_post(slug):
    post = BlogPost.query.filter_by(slug=slug).first_or_404()
    return jsonify(post.to_dict())


@bp.get("/posts/featured")
def api_featured_posts():
    posts = (
        BlogPost.query.filter_by(published=True, featured=True)
        .order_by(BlogPost.published_at.desc())
        .limit(3)
        .all()
    )
    return jsonify([post.to_dict() for post in posts])
