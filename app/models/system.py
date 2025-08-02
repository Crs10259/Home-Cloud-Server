from datetime import datetime
from typing import Any
from app.models.user import db

class SystemMetric(db.Model):
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)
    network_rx = db.Column(db.BigInteger)
    network_tx = db.Column(db.BigInteger)
    active_connections = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'network_rx': self.network_rx,
            'network_tx': self.network_tx,
            'active_connections': self.active_connections,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    value_type = db.Column(db.String(20), default='string')  # string, integer, float, boolean
    description = db.Column(db.Text, nullable=True)
    is_advanced = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def get_typed_value(self) -> Any:
        if self.value is None:
            return None
        
        if self.value_type == 'integer':
            return int(self.value)
        elif self.value_type == 'float':
            return float(self.value)
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', 'yes', 'y', '1')
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