"""
Database utility functions and decorators for consistent error handling.
"""
import logging
from functools import wraps

from flask import current_app, flash, redirect, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from blog_app.extensions import db

logger = logging.getLogger(__name__)


def handle_db_operations(success_message="Operation completed successfully!",
                        error_message="An error occurred. Please try again.",
                        redirect_url=None):
    """
    Decorator to handle database operations with consistent error handling.

    Args:
        success_message: Message to flash on success
        error_message: Message to flash on error
        redirect_url: URL to redirect to on error (if None, returns to current page)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                db.session.commit()
                flash(success_message, "success")
                return result
            except IntegrityError as e:
                db.session.rollback()
                error_msg = "Data integrity error. The operation conflicts with existing data."
                logger.error(f"IntegrityError in {func.__name__}: {str(e)}")
                flash(error_msg, "error")
                if redirect_url:
                    return redirect(url_for(redirect_url))
                return None
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"SQLAlchemyError in {func.__name__}: {str(e)}")
                flash(error_message, "error")
                if redirect_url:
                    return redirect(url_for(redirect_url))
                return None
            except Exception as e:
                db.session.rollback()
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                flash(error_message, "error")
                if redirect_url:
                    return redirect(url_for(redirect_url))
                return None
        return wrapper
    return decorator


def safe_db_commit():
    """
    Safely commit database session with error handling.

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        db.session.commit()
        return True, None
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"IntegrityError during commit: {str(e)}")
        return False, "Data integrity error. The operation conflicts with existing data."
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"SQLAlchemyError during commit: {str(e)}")
        return False, "Database error occurred. Please try again."
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error during commit: {str(e)}")
        return False, "An unexpected error occurred. Please try again."


def safe_db_add(obj, success_message="Item added successfully!", error_message="Failed to add item."):
    """
    Safely add object to database session and commit.

    Args:
        obj: Database object to add
        success_message: Message to flash on success
        error_message: Message to flash on error

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        db.session.add(obj)
        success, error = safe_db_commit()
        if success:
            flash(success_message, "success")
            return True, None
        else:
            flash(error, "error")
            return False, error
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding object to database: {str(e)}")
        flash(error_message, "error")
        return False, error_message
