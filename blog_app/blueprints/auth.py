import logging
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from blog_app.extensions import db, oauth
from blog_app.utils.database import safe_db_add, safe_db_commit
from models import User

logger = logging.getLogger(__name__)

bp = Blueprint("auth", __name__)


@bp.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.admin_dashboard"))
    return render_template("login.html")


@bp.route("/auth/github")
def github_login():
    client = oauth.create_client("github")
    redirect_uri = url_for("auth.github_callback", _external=True)
    return client.authorize_redirect(redirect_uri)


@bp.route("/auth/github/callback")
def github_callback():
    client = oauth.create_client("github")
    try:
        token = client.authorize_access_token()

        # Get user profile with timeout and error handling
        try:
            resp = client.get("https://api.github.com/user", token=token, timeout=30)
            resp.raise_for_status()
            profile = resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch GitHub user profile: {str(e)}")
            flash("Failed to fetch user profile from GitHub. Please try again.", "error")
            return redirect(url_for("auth.login"))

        # Get user emails with timeout and error handling
        try:
            email_resp = client.get("https://api.github.com/user/emails", token=token, timeout=30)
            email_resp.raise_for_status()
            emails = email_resp.json()
            primary_email = next((email["email"] for email in emails if email.get("primary")), None)
        except Exception as e:
            logger.error(f"Failed to fetch GitHub user emails: {str(e)}")
            # Continue without email - not critical for login
            primary_email = None

        github_id = str(profile["id"])
        username = profile["login"]

        user = User.query.filter_by(github_id=github_id).first()
        from flask import current_app

        if not user:
            user = User(
                github_id=github_id,
                username=username,
                email=primary_email,
                avatar_url=profile.get("avatar_url"),
            )
            if (
                current_app.config.get("ADMIN_GITHUB_USERNAME")
                and username == current_app.config["ADMIN_GITHUB_USERNAME"]
            ):
                user.is_admin = True
            try:
                success, error = safe_db_add(user, f"Welcome {username}! Your account has been created.", "Failed to create user account")
                if not success:
                    flash(error, "error")
                    return redirect(url_for("auth.login"))
            except Exception as e:
                logger.error(f"Error creating user {username}: {str(e)}")
                flash("Failed to create user account. Please try again.", "error")
                return redirect(url_for("auth.login"))
        else:
            user.username = username
            user.email = primary_email
            user.avatar_url = profile.get("avatar_url")
            user.last_login = datetime.utcnow()
            try:
                success, error = safe_db_commit()
                if not success:
                    flash(error, "error")
                    return redirect(url_for("auth.login"))
            except Exception as e:
                logger.error(f"Error updating user {username}: {str(e)}")
                flash("Failed to update user account. Please try again.", "error")
                return redirect(url_for("auth.login"))

        login_user(user)
        flash(f"Successfully logged in as {username}!", "success")
        next_page = request.args.get("next")
        return redirect(next_page) if next_page else redirect(url_for("admin.admin_dashboard"))

    except Exception as e:
        flash(f"Authentication failed: {str(e)}", "error")
        return redirect(url_for("auth.login"))


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("public.index"))
