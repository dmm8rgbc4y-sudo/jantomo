from flask import Blueprint, request
from datetime import date, timedelta
from app import create_app, db
from models import Schedule

maintenance_bp = Blueprint('maintenance', __name__)

SECRET_KEY = "cleanup_0423_secret"

@maintenance_bp.route('/__cleanup')
def cleanup():

    # 認証
    if request.args.get("key") != SECRET_KEY:
        return "Unauthorized", 403

    # Flask アプリケーションコンテキストを強制的に生成
    app = create_app()
    with app.app_context():

        cutoff = date.today() - timedelta(days=90)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        deleted = Schedule.query.filter(
            Schedule.date < cutoff_str
        ).delete()

        db.session.commit()

        return f"Cleanup OK. Deleted={deleted}"
