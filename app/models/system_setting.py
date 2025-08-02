from datetime import datetime
from typing import Any
from ..extensions import db

class SystemSetting(db.Model):
    """
    Model for storing system-wide settings.
    """
    __tablename__ = 'system_settings'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), default='string')  # string, integer, float, boolean
    description = db.Column(db.Text, nullable=True)
    is_advanced = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def __init__(self, key: str, value: str, description: str = None, value_type: str = 'string', is_advanced: bool = False, updated_by: int = None) -> None:
        self.key = key
        self.value = value
        self.description = description
        self.value_type = value_type
        self.is_advanced = is_advanced
        self.updated_by = updated_by
    
    def get_typed_value(self) -> Any:
        """Convert the string value to its actual type"""
        if self.value is None:
            return None
        
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', 'yes', 'y', '1', 't')
        else:  # string or default
            return self.value
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_typed_value(),
            'value_type': self.value_type,
            'description': self.description,
            'is_advanced': self.is_advanced,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self) -> str:
        return f'<SystemSetting {self.key}: {self.value}>' 