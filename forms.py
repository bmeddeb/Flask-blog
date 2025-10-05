from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, IntegerField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms import SubmitField


class BlogPostForm(FlaskForm):
    """Form for creating and editing blog posts."""

    title = StringField(
        "Title",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Enter post title"},
    )

    slug = StringField(
        "Slug",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "url-friendly-slug"},
    )

    excerpt = TextAreaField(
        "Excerpt",
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Short summary of the post", "rows": 3},
    )

    content = TextAreaField(
        "Content",
        validators=[DataRequired()],
        render_kw={"placeholder": "Write your post content here...", "rows": 15},
    )

    author = StringField(
        "Author",
        validators=[DataRequired(), Length(max=100)],
        render_kw={"placeholder": "Author name"},
    )

    category = SelectField("Category", choices=[], validators=[Optional()])

    tags = StringField(
        "Tags",
        validators=[Optional(), Length(max=200)],
        render_kw={"placeholder": "Comma-separated tags (e.g., python, flask, web)"},
    )

    published = BooleanField("Published")

    featured = BooleanField("Featured")

    published_at = DateTimeLocalField(
        "Published At",
        format="%Y-%m-%dT%H:%M",
        validators=[Optional()],
        render_kw={"placeholder": "YYYY-MM-DDTHH:MM"},
    )


class CategoryForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    slug = StringField("Slug", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Save")


class TagForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    slug = StringField("Slug", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Save")


class SettingsForm(FlaskForm):
    """Form for application settings."""

    # Image processing settings
    image_max_width = IntegerField(
        "Maximum Image Width",
        validators=[DataRequired(), NumberRange(min=100, max=4000)],
        render_kw={"placeholder": "1920"},
    )

    image_max_height = IntegerField(
        "Maximum Image Height",
        validators=[DataRequired(), NumberRange(min=100, max=4000)],
        render_kw={"placeholder": "1920"},
    )

    image_quality = IntegerField(
        "JPEG Quality",
        validators=[DataRequired(), NumberRange(min=1, max=100)],
        render_kw={"placeholder": "85"},
    )


class PageForm(FlaskForm):
    """Form for creating and editing pages."""

    title = StringField(
        "Page Title",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "Enter page title"},
    )

    slug = StringField(
        "URL Slug",
        validators=[DataRequired(), Length(max=200)],
        render_kw={"placeholder": "url-friendly-slug"},
    )

    layout = SelectField(
        "Page Layout",
        choices=[
            ("full-width", "Full Width - No sidebar"),
            ("sidebar-left", "Sidebar Left - Content on right"),
            ("sidebar-right", "Sidebar Right - Content on left"),
            ("blank", "Blank - Full HTML (no base template)"),
        ],
        validators=[DataRequired()],
    )

    content_type = SelectField(
        "Content Type",
        choices=[
            ("markdown", "Markdown"),
            ("html", "HTML"),
        ],
        validators=[DataRequired()],
    )

    content = TextAreaField(
        "Page Content",
        validators=[DataRequired()],
        render_kw={"placeholder": "Write your page content here...", "rows": 15},
    )

    sidebar_content = TextAreaField(
        "Sidebar Content",
        validators=[Optional()],
        render_kw={"placeholder": "Sidebar content (for sidebar layouts only)", "rows": 10},
    )

    published = BooleanField("Published")

    show_in_nav = BooleanField("Show in Navigation Menu")

    nav_order = IntegerField(
        "Navigation Order",
        validators=[Optional(), NumberRange(min=0)],
        render_kw={"placeholder": "0"},
    )
