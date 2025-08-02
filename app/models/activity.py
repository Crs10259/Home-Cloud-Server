from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, BigInteger
from sqlalchemy.orm import relationship
from ..extensions import db

class Activity(db.Model):
    """
    Model for tracking user activities including logins, file operations, and admin actions.
    """
    __tablename__ = 'activities'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(64), nullable=False)  # e.g., 'upload', 'download', 'delete'
    target = db.Column(db.String(255))  # Target of the action (e.g., file/folder name)
    details = db.Column(db.Text)  # Additional details about the action
    ip_address = db.Column(db.String(50), nullable=True)  # IP address of the user
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Transfer information (for uploads/downloads)
    file_size = db.Column(db.BigInteger, nullable=True)  # Size in bytes
    duration = db.Column(db.Float, nullable=True)  # Duration in seconds
    transfer_speed = db.Column(db.Float, nullable=True)  # Speed in bytes/second
    file_type = db.Column(db.String(50), nullable=True)  # Type of file
    
    def __init__(self, user_id: int, action: str, target: str = None, details: str = None, ip_address: str = None, 
                 file_size: int = None, duration: float = None, transfer_speed: float = None, file_type: str = None) -> None:
        self.user_id = user_id
        self.action = action
        self.target = target
        self.details = details
        self.ip_address = ip_address
        self.file_size = file_size
        self.duration = duration
        self.transfer_speed = transfer_speed
        self.file_type = file_type
    
    def __repr__(self) -> str:
        return f'<Activity {self.id}: {self.action}>'

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'target': self.target,
            'details': self.details,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'file_size': self.file_size,
            'duration': self.duration,
            'transfer_speed': self.transfer_speed,
            'file_type': self.file_type
        } 