from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class BlogPostForm(FlaskForm):
    """Form for creating and editing blog posts."""

    title = StringField(
        'Title',
        validators=[DataRequired(), Length(max=200)],
        render_kw={'placeholder': 'Enter post title'}
    )

    slug = StringField(
        'Slug',
        validators=[DataRequired(), Length(max=200)],
        render_kw={'placeholder': 'url-friendly-slug'}
    )

    excerpt = TextAreaField(
        'Excerpt',
        validators=[Optional(), Length(max=500)],
        render_kw={'placeholder': 'Short summary of the post', 'rows': 3}
    )

    content = TextAreaField(
        'Content',
        validators=[DataRequired()],
        render_kw={'placeholder': 'Write your post content here...', 'rows': 15}
    )

    author = StringField(
        'Author',
        validators=[DataRequired(), Length(max=100)],
        render_kw={'placeholder': 'Author name'}
    )

    category = SelectField(
        'Category',
        choices=[
            ('', 'Select category'),
            ('technology', 'Technology'),
            ('programming', 'Programming'),
            ('tutorial', 'Tutorial'),
            ('news', 'News'),
            ('personal', 'Personal'),
        ],
        validators=[Optional()]
    )

    tags = StringField(
        'Tags',
        validators=[Optional(), Length(max=200)],
        render_kw={'placeholder': 'Comma-separated tags (e.g., python, flask, web)'}
    )

    published = BooleanField('Published')

    featured = BooleanField('Featured')


class SettingsForm(FlaskForm):
    """Form for application settings."""

    # Image processing settings
    image_max_width = IntegerField(
        'Maximum Image Width',
        validators=[DataRequired(), NumberRange(min=100, max=4000)],
        render_kw={'placeholder': '1920'}
    )

    image_max_height = IntegerField(
        'Maximum Image Height',
        validators=[DataRequired(), NumberRange(min=100, max=4000)],
        render_kw={'placeholder': '1920'}
    )

    image_quality = IntegerField(
        'JPEG Quality',
        validators=[DataRequired(), NumberRange(min=1, max=100)],
        render_kw={'placeholder': '85'}
    )
