import logging
import os
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from markupsafe import Markup
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from blog_app.extensions import db
from blog_app.utils.database import safe_db_add, safe_db_commit
from blog_app.utils.images import (
    allowed_file,
    is_svg_filename,
    process_image,
    unique_image_name,
)
from blog_app.utils.markdown import render_markdown
from forms import BlogPostForm, CategoryForm, PageForm, SettingsForm, TagForm
from models import BlogPost, Category, Page, Setting, Tag

logger = logging.getLogger(__name__)

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
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category.choices = [("", "Select category")] + [(str(c.id), c.name) for c in categories]
    if form.validate_on_submit():
        post = BlogPost(
            title=form.title.data,
            slug=form.slug.data,
            content=form.content.data,
            excerpt=form.excerpt.data,
            author=form.author.data,
            published=form.published.data,
            featured=form.featured.data,
            user_id=current_user.id,
        )
        if form.category.data:
            post.category_obj = Category.query.get(int(form.category.data))
        tag_names = [t.strip() for t in (form.tags.data or "").split(',') if t.strip()]
        if tag_names:
            existing = {t.name: t for t in Tag.query.filter(Tag.name.in_(tag_names)).all()}
            for name in tag_names:
                tag = existing.get(name)
                if not tag:
                    tag = Tag(name=name)
                    db.session.add(tag)
                post.tag_items.append(tag)
        if form.published.data:
            post.published_at = datetime.utcnow()

        try:
            db.session.add(post)
            success, error = safe_db_commit()
            if not success:
                flash(error, "error")
                return render_template("admin/post_form.html", form=form, title="New Post")

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
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            flash("Failed to create post. Please try again.", "error")
            return render_template("admin/post_form.html", form=form, title="New Post")
    form.author.data = "Admin"
    return render_template("admin/post_form.html", form=form, title="New Post")


@bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_post(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm(obj=post)
    categories = Category.query.order_by(Category.name.asc()).all()
    form.category.choices = [("", "Select category")] + [(str(c.id), c.name) for c in categories]
    if request.method == 'GET':
        form.category.data = str(post.category_obj.id) if getattr(post, 'category_obj', None) else ""
        if getattr(post, 'tag_items', None):
            form.tags.data = ", ".join(t.name for t in post.tag_items)
    if form.validate_on_submit():
        post.title = form.title.data
        post.slug = form.slug.data
        post.content = form.content.data
        post.excerpt = form.excerpt.data
        post.author = form.author.data
        if form.category.data:
            post.category_obj = Category.query.get(int(form.category.data))
        else:
            post.category_obj = None
        # Replace tag relations
        post.tag_items.clear()
        tag_names = [t.strip() for t in (form.tags.data or "").split(',') if t.strip()]
        if tag_names:
            existing = {t.name: t for t in Tag.query.filter(Tag.name.in_(tag_names)).all()}
            for name in tag_names:
                tag = existing.get(name)
                if not tag:
                    tag = Tag(name=name)
                    db.session.add(tag)
                post.tag_items.append(tag)
        was_published = post.published
        post.published = form.published.data
        if form.published.data and not was_published:
            post.published_at = datetime.utcnow()
        post.featured = form.featured.data

        try:
            success, error = safe_db_commit()
            if not success:
                flash(error, "error")
                return render_template("admin/post_form.html", form=form, title="Edit Post", post=post)

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
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {str(e)}")
            flash("Failed to update post. Please try again.", "error")
            return render_template("admin/post_form.html", form=form, title="Edit Post", post=post)
    return render_template("admin/post_form.html", form=form, title="Edit Post", post=post)


# =====================
# Taxonomy management
# =====================

@bp.route('/taxonomies/categories', methods=['GET', 'POST'])
@login_required
def admin_categories():
    form = CategoryForm()
    if form.validate_on_submit():
        # create new category
        cat = Category(name=form.name.data.strip(), slug=(form.slug.data or '').strip() or None)
        try:
            success, error = safe_db_add(cat, 'Category created', 'Failed to create category')
            if success:
                return redirect(url_for('admin.admin_categories'))
        except Exception as e:
            logger.error(f"Error creating category: {str(e)}")
            flash("Failed to create category. Please try again.", "error")
    categories = Category.query.order_by(Category.name.asc()).all()
    return render_template('admin/categories.html', categories=categories, form=form)


@bp.route('/taxonomies/categories/<int:cat_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        cat.name = form.name.data.strip()
        cat.slug = (form.slug.data or '').strip() or None
        try:
            success, error = safe_db_commit()
            if success:
                flash('Category updated', 'success')
                return redirect(url_for('admin.admin_categories'))
            else:
                flash(error, 'error')
        except Exception as e:
            logger.error(f"Error updating category {cat_id}: {str(e)}")
            flash("Failed to update category. Please try again.", "error")
    return render_template('admin/category_form.html', form=form, category=cat, title='Edit Category')


@bp.route('/taxonomies/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
def admin_delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.posts:
        flash('Cannot delete a category in use by posts.', 'error')
        return redirect(url_for('admin.admin_categories'))
    try:
        db.session.delete(cat)
        success, error = safe_db_commit()
        if success:
            flash('Category deleted', 'success')
        else:
            flash(error, 'error')
    except Exception as e:
        logger.error(f"Error deleting category {cat_id}: {str(e)}")
        flash("Failed to delete category. Please try again.", "error")
    return redirect(url_for('admin.admin_categories'))


@bp.route('/taxonomies/tags', methods=['GET', 'POST'])
@login_required
def admin_tags():
    form = TagForm()
    if form.validate_on_submit():
        tag_name = form.name.data.strip()
        # Check if tag already exists
        existing_tag = Tag.query.filter_by(name=tag_name).first()
        if existing_tag:
            flash(f'Tag "{tag_name}" already exists', 'error')
        else:
            tag = Tag(name=tag_name, slug=(form.slug.data or '').strip() or None)
            try:
                success, error = safe_db_add(tag, 'Tag created', 'Failed to create tag')
                if not success:
                    flash(error, 'error')
            except Exception as e:
                logger.error(f"Error creating tag: {str(e)}")
                flash("Failed to create tag. Please try again.", "error")
        return redirect(url_for('admin.admin_tags'))
    tags = Tag.query.order_by(Tag.name.asc()).all()
    return render_template('admin/tags.html', tags=tags, form=form)


@bp.route('/taxonomies/tags/<int:tag_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    form = TagForm(obj=tag)
    if form.validate_on_submit():
        tag.name = form.name.data.strip()
        tag.slug = (form.slug.data or '').strip() or None
        try:
            success, error = safe_db_commit()
            if success:
                flash('Tag updated', 'success')
            else:
                flash(error, 'error')
        except Exception as e:
            logger.error(f"Error updating tag {tag_id}: {str(e)}")
            flash("Failed to update tag. Please try again.", "error")
        return redirect(url_for('admin.admin_tags'))
    return render_template('admin/tag_form.html', form=form, tag=tag, title='Edit Tag')


@bp.route('/taxonomies/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def admin_delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    if tag.posts:
        flash('Cannot delete a tag in use by posts.', 'error')
        return redirect(url_for('admin.admin_tags'))
    try:
        db.session.delete(tag)
        success, error = safe_db_commit()
        if success:
            flash('Tag deleted', 'success')
        else:
            flash(error, 'error')
    except Exception as e:
        logger.error(f"Error deleting tag {tag_id}: {str(e)}")
        flash("Failed to delete tag. Please try again.", "error")
    return redirect(url_for('admin.admin_tags'))


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
        try:
            Setting.set(
                "image_max_width", form.image_max_width.data, "Maximum width for uploaded images"
            )
            Setting.set(
                "image_max_height", form.image_max_height.data, "Maximum height for uploaded images"
            )
            Setting.set("image_quality", form.image_quality.data, "JPEG quality (1-100)")
            flash("Settings updated successfully!", "success")
            return redirect(url_for("admin.admin_settings"))
        except ValueError as e:
            flash(f"Error updating settings: {str(e)}", "error")
        except Exception as e:
            logger.error(f"Unexpected error updating settings: {str(e)}")
            flash("Failed to update settings. Please try again.", "error")
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
        try:
            success, error = safe_db_add(page, "Page created successfully!", "Failed to create page")
            if success:
                return redirect(url_for("admin.admin_pages"))
        except Exception as e:
            logger.error(f"Error creating page: {str(e)}")
            flash("Failed to create page. Please try again.", "error")
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
        try:
            success, error = safe_db_commit()
            if success:
                flash("Page updated successfully!", "success")
                return redirect(url_for("admin.admin_pages"))
            else:
                flash(error, "error")
        except Exception as e:
            logger.error(f"Error updating page {page_id}: {str(e)}")
            flash("Failed to update page. Please try again.", "error")
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
    try:
        success, error = safe_db_commit()
        if success:
            flash("Page published successfully!", "success")
            return redirect(url_for("public.view_page", slug=page.slug))
        else:
            flash(error, "error")
    except Exception as e:
        logger.error(f"Error publishing page {page_id}: {str(e)}")
        flash("Failed to publish page. Please try again.", "error")
    return redirect(url_for("admin.admin_pages"))


@bp.route("/pages/<int:page_id>/delete", methods=["POST"])
@login_required
def admin_delete_page(page_id):
    page = Page.query.get_or_404(page_id)
    try:
        db.session.delete(page)
        success, error = safe_db_commit()
        if success:
            flash("Page deleted successfully!", "success")
        else:
            flash(error, "error")
    except Exception as e:
        logger.error(f"Error deleting page {page_id}: {str(e)}")
        flash("Failed to delete page. Please try again.", "error")
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
    # TODO(svg): When an SVG sanitizer is available, handle `.svg` here
    # by sanitizing and saving as SVG. This stub explicitly blocks SVG
    # uploads unless the feature flag is enabled and sanitizer provided.
    if file and allowed_file(file.filename, allowed):
        # Controlled SVG branch
        if is_svg_filename(file.filename):
            if not current_app.config.get("SVG_SANITIZATION_ENABLED", False):
                return (
                    jsonify({
                        "error": "SVG sanitization disabled. Set SVG_SANITIZATION_ENABLED=1 and provide a sanitizer to accept SVGs."
                    }),
                    400,
                )
            return jsonify({"error": "SVG sanitization not implemented yet."}), 501

        upload_dir: Path = current_app.config["UPLOAD_FOLDER"]
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to create upload directory: {str(e)}")
            return jsonify({"error": "Failed to create upload directory"}), 500

        # Save and process raster images as JPEG
        filename = unique_image_name("jpg")
        filepath = upload_dir / filename
        try:
            file.save(filepath)
        except (OSError, IOError) as e:
            logger.error(f"Failed to save uploaded file: {str(e)}")
            return jsonify({"error": "Failed to save uploaded file"}), 500

        try:
            process_image(
                filepath,
                int(Setting.get("image_max_width", current_app.config["IMAGE_MAX_WIDTH"])),
                int(Setting.get("image_max_height", current_app.config["IMAGE_MAX_HEIGHT"])),
                int(Setting.get("image_quality", current_app.config["IMAGE_QUALITY"])),
            )
        except ValueError as e:
            # Clean up the saved file if processing failed
            try:
                filepath.unlink(missing_ok=True)
            except OSError as cleanup_error:
                logger.error(f"Failed to cleanup file {filepath}: {str(cleanup_error)}")
            return jsonify({"error": f"Image processing failed: {str(e)}"}), 400
        except Exception as e:
            # Clean up the saved file if processing failed
            try:
                filepath.unlink(missing_ok=True)
            except OSError as cleanup_error:
                logger.error(f"Failed to cleanup file {filepath}: {str(cleanup_error)}")
            logger.error(f"Unexpected error processing image: {str(e)}")
            return jsonify({"error": "Image processing failed due to an unexpected error"}), 500

        url = url_for("static", filename=f"uploads/{filename}")
        return jsonify({"url": url})
    return jsonify({"error": "Invalid file type"}), 400
