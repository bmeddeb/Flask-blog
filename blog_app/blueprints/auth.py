from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from blog_app.extensions import db, oauth
from models import User

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
        resp = client.get("https://api.github.com/user", token=token)
        profile = resp.json()

        email_resp = client.get("https://api.github.com/user/emails", token=token)
        emails = email_resp.json()
        primary_email = next((email["email"] for email in emails if email.get("primary")), None)

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
            db.session.add(user)
            db.session.commit()
            flash(f"Welcome {username}! Your account has been created.", "success")
        else:
            user.username = username
            user.email = primary_email
            user.avatar_url = profile.get("avatar_url")
            user.last_login = datetime.utcnow()
            db.session.commit()

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
