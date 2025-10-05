import re
from typing import Optional, Type

from flask_sqlalchemy import SQLAlchemy


_slug_re = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = _slug_re.sub("-", s)
    s = s.strip("-")
    return s or "item"


def ensure_unique_slug(model: Type, base_slug: str, exclude_id: Optional[int] = None) -> str:
    """Generate a unique slug for a SQLAlchemy model with `slug` column.

    - model: SQLAlchemy model class with `slug` column
    - base_slug: proposed slug (already slugified)
    - exclude_id: primary key to exclude (for edits)
    """
    slug = base_slug
    i = 2
    from sqlalchemy import and_

    while True:
        q = model.query.filter(model.slug == slug)
        if exclude_id is not None:
            q = q.filter(model.id != exclude_id)
        exists = q.first()
        if not exists:
            return slug
        slug = f"{base_slug}-{i}"
        i += 1

