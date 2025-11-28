# app.py

from flask import Flask, redirect, url_for, send_from_directory
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
import os

# 🔹 db を models から読み込む（正しい構成）
from models.db import db

login_manager = LoginManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.secret_key = "secret-key"

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

    # --- モデル読み込み（db.create_all() のために必要） ---
    from models.models import User
    from models.friend import Friend
    from models.friend_request import FriendRequest
    from models.device import Device

    # --- Blueprint を個別 import（循環防止） ---
    from routes.auth import auth_bp
    from routes.schedule import schedule_bp
    from routes.profile import profile_bp
    from routes.friend import friend_bp
    from routes.main import main_bp
    from maintenance import maintenance_bp

    # --- Blueprint登録 ---
    app.register_blueprint(auth_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(friend_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(main_bp)

    # --- Flask-Login 未ログイン時の挙動 ---
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

    # --- ルート一覧 ---
    print("=== Registered Routes ===")
    for r in app.url_map.iter_rules():
        print(r, "→", r.endpoint)
    print("=========================")

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
