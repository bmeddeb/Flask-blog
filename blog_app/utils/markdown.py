import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension


def render_markdown(text: str) -> str:
    """Convert markdown to HTML with syntax highlighting and LaTeX math support."""
    md = markdown.Markdown(
        extensions=[
            FencedCodeExtension(),
            CodeHiliteExtension(css_class="highlight", linenums=False),
            TableExtension(),
            "nl2br",
            "sane_lists",
            "mdx_math",  # LaTeX math support
        ],
        extension_configs={
            "mdx_math": {
                "enable_dollar_delimiter": True,  # Enable $...$ for inline math
            }
        },
    )
    return md.convert(text or "")
