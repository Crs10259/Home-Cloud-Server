from app.models.user import User
from app.models.file import File, Folder
from app.models.system import SystemMetric, SystemSetting
from app.models.activity import Activity
from app.extensions import db
from werkzeug.security import generate_password_hash
import os

def initialize_db(app):
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Check if admin user already exists
        admin_exists = User.query.filter_by(username='admin').first()
        if not admin_exists:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                storage_quota=10 * 1024 * 1024 * 1024  # 10 GB
            )
            db.session.add(admin)
            
            # Create default folders for admin
            admin_root_folder = Folder(
                name='root',
                user_id=1  # Admin's ID (first user)
            )
            db.session.add(admin_root_folder)
            
            # Create default system settings
            default_settings = [
                SystemSetting(key='max_upload_size', value='1073741824', value_type='integer', description='Maximum file size for upload (bytes)', is_advanced=False),
                SystemSetting(key='default_user_quota', value='5368709120', value_type='integer', description='Default storage quota for new users (bytes)', is_advanced=False),
                SystemSetting(key='allowed_file_types', value='*', value_type='string', description='Comma-separated list of allowed file extensions (* for all)', is_advanced=True),
                SystemSetting(key='enable_registration', value='true', value_type='boolean', description='Allow new user registrations', is_advanced=False),
                SystemSetting(key='maintenance_mode', value='false', value_type='boolean', description='Put the system in maintenance mode', is_advanced=True)
            ]
            
            for setting in default_settings:
                db.session.add(setting)
            
            db.session.commit()
        
        return db 