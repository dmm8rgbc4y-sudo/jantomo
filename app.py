# --- ライブラリのインポート ---
from flask import Flask, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
import os

# --- グローバル変数の定義 ---
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

# --- アプリケーションの作成 ---
def create_app():
    app = Flask(__name__)
    app.secret_key = 'secret-key'
    
    # --- DB格納場所の設定 ---
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    default_db = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'jantomo.db')}"
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', default_db
    ).replace("postgres://", "postgresql://")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- グローバル変数の初期化 ---
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # --- モデル・ルートをインポート ---
    from models.models import User
    from models.friend import Friend
    from models.friend_request import FriendRequest
    from routes import auth, schedule, profile, friend

    # --- Blueprint登録 ---
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(schedule.schedule_bp)
    app.register_blueprint(profile.profile_bp)
    app.register_blueprint(friend.friend_bp)

    # --- Flask-Loginのユーザーローダー登録 ---
    @login_manager.user_loader
    def load_user(user_id):
        """セッション内のuser_idからユーザーを復元"""
        return User.query.get(int(user_id))

    # --- トップページ（ログイン状態で遷移先を振り分け） ---
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('schedule.weekly'))
        return redirect(url_for('auth.register'))

    # --- Service Workerをルートパスで配信 ---
    @app.route('/sw.js')
    def service_worker():
        """Service Workerをルートパスで返す"""
        return send_from_directory('static/js', 'sw.js')

    return app


# --- アプリ起動 ---
if __name__ == '__main__':
    app = create_app()

    # 🚀 Renderデプロイ時にPostgreSQLのテーブルを自動作成
    with app.app_context():
        db.create_all()
        
    app.run(debug=True)
