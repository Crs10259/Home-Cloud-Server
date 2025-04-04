from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from ..extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # 'user' or 'admin'
    storage_quota = db.Column(db.BigInteger, default=5 * 1024 * 1024 * 1024)  # 5GB default
    storage_used = db.Column(db.BigInteger, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    trash_retention_days = db.Column(db.Integer, default=30)  # Default 30 days for trash retention
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_storage_usage_percent(self):
        if self.storage_quota > 0:
            return (self.storage_used / self.storage_quota) * 100
        return 100
    
    def update_storage_used(self):
        """Update the user's storage usage by calculating the total size of their files"""
        from app.models.file import File
        total_size = db.session.query(db.func.sum(File.size)).filter_by(user_id=self.id).scalar() or 0
        self.storage_used = total_size
        db.session.commit()
        return self.storage_used
    
    def has_space_for_file(self, file_size):
        """Check if user has enough space for a file of the given size"""
        return (self.storage_used + file_size) <= self.storage_quota 