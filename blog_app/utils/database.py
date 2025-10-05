from typing import Tuple, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from blog_app.extensions import db


def safe_db_commit() -> Tuple[bool, Optional[str]]:
    try:
        db.session.commit()
        return True, None
    except IntegrityError as e:
        db.session.rollback()
        return False, "Database constraint error. Please ensure values are unique and valid."
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, "Database error. Please try again."


def safe_db_add(instance, success_message: str = "", error_message: str = "") -> Tuple[bool, Optional[str]]:
    try:
        db.session.add(instance)
        db.session.commit()
        return True, None
    except IntegrityError as e:
        db.session.rollback()
        return False, "Database constraint error. Please ensure values are unique and valid."
    except SQLAlchemyError as e:
        db.session.rollback()
        return False, "Database error. Please try again."

