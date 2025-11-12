from flask_login import UserMixin
from datetime import datetime, timezone
from app import db  # app.pyからdbをインポート

# --- Userモデル ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    device_token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    schedules = db.relationship('Schedule', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

# --- Scheduleモデル ---
class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # ondelete='CASCADE' を追加
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )
    date = db.Column(db.String(20), nullable=False)
    time_type = db.Column(db.String(10), nullable=False)  # '昼', '夜', '両方'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Schedule {self.date} ({self.time_type})>'
