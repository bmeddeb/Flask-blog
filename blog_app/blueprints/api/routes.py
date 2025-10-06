from flask import Blueprint, jsonify, request
from models import Post

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.get("/posts")
def api_posts():
    published_only = request.args.get("published", "true").lower() == "true"
    if published_only:
        posts = (
            Post.query.filter_by(post_type='post', post_status='publish')
            .order_by(Post.published_at.desc()).all()
        )
    else:
        posts = Post.query.filter_by(post_type='post').order_by(Post.created_at.desc()).all()
    return jsonify([post.to_dict() for post in posts])


@bp.get("/posts/<slug>")
def api_post(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    return jsonify(post.to_dict())


@bp.get("/posts/featured")
def api_featured_posts():
    posts = (
        Post.query.filter_by(post_type='post', post_status='publish', featured=True)
        .order_by(Post.published_at.desc())
        .limit(3)
        .all()
    )
    return jsonify([post.to_dict() for post in posts])
