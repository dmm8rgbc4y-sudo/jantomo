# app.py

from flask import Flask, redirect, url_for, send_from_directory
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect   # 🔐 CSRFProtect を追加
import os

# 🔹 db を models から読み込む
from models.db import db

login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()   # 🔐 CSRFインスタンス作成


def create_app():
    app = Flask(__name__)
    app.secret_key = "secret-key"

    # --- GA4 設定 ---
    app.config["GA4_ID"] = "G-0JVEJFNN2L"

    # --- Cookie セキュリティ属性（最優先①対応） ---
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,        # HTTPS のみ送信（Render 本番 OK）
        SESSION_COOKIE_SAMESITE="Lax",     # CSRF 攻撃を防止
    )

    # --- DB格納場所の設定 ---
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
    csrf.init_app(app)          # 🔐 CSRF を Flask に有効化（最優先②対応）

    # --- GA4 をテンプレートへ渡す ---
    @app.context_processor
    def inject_ga4():
        return dict(GA4_ID=app.config.get("GA4_ID"))

    # --- モデル読み込み ---
    from models.models import User
    from models.friend import Friend
    from models.friend_request import FriendRequest
    from models.device import Device

    # --- Blueprint ---
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

    # --- Flask-Login 未ログイン時 ---
    @login_manager.unauthorized_handler
    def unauthorized():
        return redirect(url_for("main.landing"))

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- トップページ ---
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("schedule.weekly"))
        return redirect(url_for("main.landing"))

    # --- Service Worker ---
    @app.route("/sw.js")
    def service_worker():
        return send_from_directory("static/js", "sw.js")

    # --- auto_login / LP誘導 ---
    from routes.auth import auto_login, force_register_if_not_logged_in
    app.before_request(auto_login)
    app.before_request(force_register_if_not_logged_in)

    # --- Routes debug print ---
    print("=== Registered Routes ===")
    for r in app.url_map.iter_rules():
        print(r, "→", r.endpoint)
    print("=========================")

    # ======================================================
    # 🔐 セキュリティヘッダー追加（HSTS / XFO / nosniff）
    # ======================================================
    @app.after_request
    def add_security_headers(response):
        # HSTS（HTTPS 強制）※本番のみ Secure と併用
        response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains'

        # クリックジャッキング対策
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'

        # MIME スニッフィング防止
        response.headers['X-Content-Type-Options'] = 'nosniff'

        return response

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
