from app import db
from datetime import datetime

class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    roblox_cookie = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.String(50), nullable=True)
    totp_secret = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserSession {self.username}>'
