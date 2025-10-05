import os
from datetime import datetime
from pathlib import Path
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    jsonify,
)
from flask_login import login_required, current_user
from markupsafe import Markup

from blog_app.extensions import db
from blog_app.utils.markdown import render_markdown
from blog_app.utils.images import allowed_file, process_image, unique_image_name
from models import BlogPost, Page, Setting
from forms import BlogPostForm, PageForm, SettingsForm

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@login_required
def admin_dashboard():
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).all()
    return render_template("admin/dashboard.html", posts=posts)


@bp.route("/posts/new", methods=["GET", "POST"])
@login_required
def admin_new_post():
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
            user_id=current_user.id,
        )
        if form.published.data:
            post.published_at = datetime.utcnow()
        db.session.add(post)
        db.session.commit()
        if form.published.data:
            view_url = url_for("public.blog_post", slug=post.slug)
            flash(
                Markup(
                    f'Post created successfully! <a href="{view_url}" target="_blank" style="color: #155724; text-decoration: underline; font-weight: 600;">View Post →</a>'
                ),
                "success",
            )
        else:
            flash("Post created successfully as draft!", "success")
        return redirect(url_for("admin.admin_dashboard"))
    form.author.data = "Admin"
    return render_template("admin/post_form.html", form=form, title="New Post")


@bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_post(post_id):
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
        was_published = post.published
        post.published = form.published.data
        if form.published.data and not was_published:
            post.published_at = datetime.utcnow()
        post.featured = form.featured.data
        db.session.commit()
        if form.published.data:
            view_url = url_for("public.blog_post", slug=post.slug)
            flash(
                Markup(
                    f'Post updated successfully! <a href="{view_url}" target="_blank" style="color: #155724; text-decoration: underline; font-weight: 600;">View Post →</a>'
                ),
                "success",
            )
        else:
            flash("Post updated successfully!", "success")
        return redirect(url_for("admin.admin_dashboard"))
    return render_template("admin/post_form.html", form=form, title="Edit Post", post=post)


@bp.route("/posts/<int:post_id>/preview")
@login_required
def admin_preview_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    post_html = render_markdown(post.content)
    return render_template("blog_post.html", post=post, post_html=post_html, is_preview=True)


@bp.route("/posts/<int:post_id>/publish", methods=["POST"])
@login_required
def admin_publish_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    if not post.is_owned_by(current_user):
        flash("You do not have permission to publish this post.", "error")
        return redirect(url_for("admin.admin_dashboard"))
    post.published = True
    post.published_at = datetime.utcnow()
    db.session.commit()
    flash(
        Markup(
            f'Post published successfully! <a href="{url_for("public.blog_post", slug=post.slug)}" target="_blank" style="color: #155724; text-decoration: underline; font-weight: 600;">View Post →</a>'
        ),
        "success",
    )
    return redirect(url_for("public.blog_post", slug=post.slug))


@bp.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def admin_delete_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully!", "success")
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    form = SettingsForm()
    if form.validate_on_submit():
        Setting.set(
            "image_max_width", form.image_max_width.data, "Maximum width for uploaded images"
        )
        Setting.set(
            "image_max_height", form.image_max_height.data, "Maximum height for uploaded images"
        )
        Setting.set("image_quality", form.image_quality.data, "JPEG quality (1-100)")
        flash("Settings updated successfully!", "success")
        return redirect(url_for("admin.admin_settings"))
    from flask import current_app

    form.image_max_width.data = int(
        Setting.get("image_max_width", current_app.config["IMAGE_MAX_WIDTH"])
    )
    form.image_max_height.data = int(
        Setting.get("image_max_height", current_app.config["IMAGE_MAX_HEIGHT"])
    )
    form.image_quality.data = int(Setting.get("image_quality", current_app.config["IMAGE_QUALITY"]))
    return render_template("admin/settings.html", form=form)


@bp.route("/pages")
@login_required
def admin_pages():
    pages = Page.query.order_by(Page.created_at.desc()).all()
    return render_template("admin/pages.html", pages=pages)


@bp.route("/pages/new", methods=["GET", "POST"])
@login_required
def admin_new_page():
    form = PageForm()
    if form.validate_on_submit():
        page = Page(
            title=form.title.data,
            slug=form.slug.data,
            content=form.content.data,
            sidebar_content=form.sidebar_content.data,
            layout=form.layout.data,
            content_type=form.content_type.data,
            published=form.published.data,
            show_in_nav=form.show_in_nav.data,
            nav_order=form.nav_order.data or 0,
            user_id=current_user.id,
        )
        if form.published.data:
            page.published_at = datetime.utcnow()
        db.session.add(page)
        db.session.commit()
        flash("Page created successfully!", "success")
        return redirect(url_for("admin.admin_pages"))
    return render_template("admin/page_form.html", form=form, title="New Page")


@bp.route("/pages/<int:page_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_page(page_id):
    page = Page.query.get_or_404(page_id)
    form = PageForm(obj=page)
    if form.validate_on_submit():
        page.title = form.title.data
        page.slug = form.slug.data
        page.content = form.content.data
        page.sidebar_content = form.sidebar_content.data
        page.layout = form.layout.data
        page.content_type = form.content_type.data
        page.show_in_nav = form.show_in_nav.data
        page.nav_order = form.nav_order.data or 0
        was_published = page.published
        page.published = form.published.data
        if form.published.data and not was_published:
            page.published_at = datetime.utcnow()
        db.session.commit()
        flash("Page updated successfully!", "success")
        return redirect(url_for("admin.admin_pages"))
    return render_template("admin/page_form.html", form=form, title="Edit Page", page=page)


@bp.route("/pages/<int:page_id>/preview")
@login_required
def admin_preview_page(page_id):
    page = Page.query.get_or_404(page_id)
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
        is_preview=True,
    )


@bp.route("/pages/<int:page_id>/publish", methods=["POST"])
@login_required
def admin_publish_page(page_id):
    page = Page.query.get_or_404(page_id)
    if not page.is_owned_by(current_user):
        flash("You do not have permission to publish this page.", "error")
        return redirect(url_for("admin.admin_pages"))
    page.published = True
    page.published_at = datetime.utcnow()
    db.session.commit()
    flash("Page published successfully!", "success")
    return redirect(url_for("public.view_page", slug=page.slug))


@bp.route("/pages/<int:page_id>/delete", methods=["POST"])
@login_required
def admin_delete_page(page_id):
    page = Page.query.get_or_404(page_id)
    db.session.delete(page)
    db.session.commit()
    flash("Page deleted successfully!", "success")
    return redirect(url_for("admin.admin_pages"))


@bp.route("/upload-image", methods=["POST"])
@login_required
def upload_image():
    from flask import current_app

    if "image" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    if file and allowed_file(file.filename, allowed):
        filename = unique_image_name()
        upload_dir: Path = current_app.config["UPLOAD_FOLDER"]
        upload_dir.mkdir(parents=True, exist_ok=True)
        filepath = upload_dir / filename
        file.save(filepath)

        try:
            process_image(
                filepath,
                int(Setting.get("image_max_width", current_app.config["IMAGE_MAX_WIDTH"])),
                int(Setting.get("image_max_height", current_app.config["IMAGE_MAX_HEIGHT"])),
                int(Setting.get("image_quality", current_app.config["IMAGE_QUALITY"])),
            )
        except Exception as e:
            filepath.unlink(missing_ok=True)
            return jsonify({"error": f"Image processing failed: {str(e)}"}), 400

        url = url_for("static", filename=f"uploads/{filename}")
        return jsonify({"url": url})
    return jsonify({"error": "Invalid file type"}), 400
