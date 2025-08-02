from datetime import datetime
from ..extensions import db

class Folder(db.Model):
    """
    Model for representing folders in the file system.
    """
    __tablename__ = 'folders'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(1024), nullable=False)  # Full path from root
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id', ondelete='CASCADE'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', back_populates='folders')
    parent = db.relationship('Folder', remote_side=[id], backref=db.backref('subfolders', cascade='all, delete-orphan'))
    files = db.relationship('File', back_populates='folder', cascade='all, delete-orphan')
    
    def __init__(self, name: str, path: str, user_id: int, parent_id: int = None) -> None:
        self.name = name
        self.path = path
        self.user_id = user_id
        self.parent_id = parent_id
    
    def __repr__(self) -> str:
        return f'<Folder {self.id}: {self.name}>' 