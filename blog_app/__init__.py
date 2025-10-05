import logging
import os
from pathlib import Path

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import current_user, login_required, login_user, logout_user

from blog_app.cli import register_cli
from blog_app.extensions import db, login_manager, migrate, oauth
from config import config as config_map
from models import Page, User


def create_app(env: str | None = None) -> Flask:
    load_dotenv()

    # Ensure Flask can find the top-level templates/static directories
    root_dir = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(root_dir / "templates"),
        static_folder=str(root_dir / "static"),
    )

    env_name = env or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_map[env_name])

    # Configure logging
    if not app.debug and not app.testing:
        # Production logging
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = logging.FileHandler('logs/blog.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Blog application startup')
    else:
        # Development logging
        logging.basicConfig(level=logging.INFO)
        app.logger.setLevel(logging.INFO)

    # Ensure upload folder exists
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access the admin panel."

    oauth.init_app(app)
    github = oauth.register(
        name="github",
        client_id=app.config.get("GITHUB_CLIENT_ID"),
        client_secret=app.config.get("GITHUB_CLIENT_SECRET"),
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        redirect_uri=app.config.get("GITHUB_CALLBACK_URL"),
        client_kwargs={"scope": "user:email"},
    )

    # Blueprints
    from blog_app.blueprints.admin.routes import bp as admin_bp
    from blog_app.blueprints.api.routes import bp as api_bp
    from blog_app.blueprints.auth import bp as auth_bp
    from blog_app.blueprints.public.routes import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)

    # Context processor
    @app.context_processor
    def inject_nav_pages():
        def get_nav_pages():
            return (
                Page.query.filter_by(published=True, show_in_nav=True)
                .order_by(Page.nav_order)
                .all()
            )

        return dict(get_nav_pages=get_nav_pages)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("500.html"), 500

    # CLI
    register_cli(app)

    # Login loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
