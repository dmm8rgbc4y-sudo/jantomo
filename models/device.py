from datetime import datetime, timezone
from app import db

class Device(db.Model):
    __tablename__ = "device"

    id = db.Column(db.Integer, primary_key=True)
    # ondelete='CASCADE' を追加
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False
    )
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)
    is_revoked = db.Column(db.Boolean, default=False)

    user = db.relationship("User", backref=db.backref("devices", lazy=True))

    def __repr__(self):
        return f"<Device user={self.user_id} revoked={self.is_revoked}>"
