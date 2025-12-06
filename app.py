# app.py

from flask import Flask, redirect, url_for, send_from_directory, request
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os

from models.db import db

login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.secret_key = "secret-key"

    # --- GA4 ---
    app.config["GA4_ID"] = "G-0JVEJFNN2L"

    # --- Cookie セキュリティ属性（本番だけ Secure=True） ---
    is_production = os.environ.get("RENDER") == "true"

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=is_production,  # ← ローカルでは False
        SESSION_COOKIE_SAMESITE="Lax",
    )

    # --- DB ---
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    default_db = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'jantomo.db')}"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", default_db
    ).replace("postgres://", "postgresql://")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- 初期化 ---
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)   # ← CSRFProtect を有効化（最重要）

    # --- GA4 テンプレート ---
    @app.context_processor
    def inject_ga4():
        return dict(GA4_ID=app.config.get("GA4_ID"))

    # --- Models ---
    from models.models import User
    from models.friend import Friend
    from models.friend_request import FriendRequest
    from models.device import Device

    # --- Blueprints ---
    from routes.auth import auth_bp
    from routes.schedule import schedule_bp
    from routes.profile import profile_bp
    from routes.friend import friend_bp
    from routes.main import main_bp
    from maintenance import maintenance_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(friend_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(main_bp)

    # ---- /register と /login の POST 時だけ auto_login を止める ----
    @app.before_request
    def skip_auto_login_for_auth_post():
        if request.path.startswith('/register') and request.method == 'POST':
            return
        if request.path.startswith('/login') and request.method == 'POST':
            return

    # --- auto_login / LP誘導 ---
    from routes.auth import auto_login, force_register_if_not_logged_in
    app.before_request(auto_login)
    app.before_request(force_register_if_not_logged_in)

    # --- Flask-Login ---
    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect(url_for("main.landing"))

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- index ---
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("schedule.weekly"))
        return redirect(url_for("main.landing"))

    # --- SW ---
    @app.route("/sw.js")
    def service_worker():
        return send_from_directory("static/js", "sw.js")

    # --- Security Headers ---
    @app.after_request
    def add_security_headers(response):
        response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
