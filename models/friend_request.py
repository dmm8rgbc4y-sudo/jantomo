from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone 
from app import db
    
# --- FriendRequestモデル ---
class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(10), default='pending')  # pending / accepted / rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<FriendRequest {self.sender_id} → {self.receiver_id} ({self.status})>'