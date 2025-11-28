from datetime import datetime, timezone
from .db import db

class Friend(db.Model):
    __tablename__ = 'friend'

    id = db.Column(db.Integer, primary_key=True)
    # 両方の外部キーに ondelete='CASCADE' を追加
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )
    friend_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )
    status = db.Column(db.String(20), default='pending')  # 承認状態を管理
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Friend {self.user_id} ↔ {self.friend_id} ({self.status})>'

    # --- 双方向検索（承認済みのみ） ---
    @staticmethod
    def get_friend_ids(user_id):
        """
        特定ユーザーの friend_id 一覧を取得（双方向対応・承認済みのみ）。
        """
        friends_as_user = Friend.query.filter_by(user_id=user_id, status='accepted').all()
        friends_as_friend = Friend.query.filter_by(friend_id=user_id, status='accepted').all()

        ids = {f.friend_id for f in friends_as_user} | {f.user_id for f in friends_as_friend}
        return list(ids)
