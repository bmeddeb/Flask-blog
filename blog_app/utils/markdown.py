import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension


def render_markdown(text: str) -> str:
    """Convert markdown to HTML with syntax highlighting."""
    md = markdown.Markdown(
        extensions=[
            FencedCodeExtension(),
            CodeHiliteExtension(css_class="highlight", linenums=False),
            TableExtension(),
            "nl2br",
            "sane_lists",
        ]
    )
    return md.convert(text or "")
