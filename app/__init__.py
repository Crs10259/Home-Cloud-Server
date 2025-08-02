# This file initializes the app package 
import os
from flask import Flask, render_template, redirect, url_for, Response
from config import config
from app.models.db_init import initialize_db
from datetime import datetime
from app.utils.system_monitor import SystemMonitor
from flask_migrate import Migrate

def create_app(config_name: str = 'default') -> Flask:
    # Specify the template folder explicitly
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    app.config.from_object(config[config_name])
    
    # Ensure custom temp directory (for large file uploads) is used system-wide
    temp_dir = app.config.get('TEMP_UPLOAD_PATH')
    if temp_dir:
        try:
            os.makedirs(temp_dir, exist_ok=True)
            # Set environment variables recognized by tempfile
            os.environ['TMPDIR'] = temp_dir
            os.environ['TEMP'] = temp_dir
            os.environ['TMP'] = temp_dir

            # Also set Python's internal default tempdir for current process
            import tempfile
            tempfile.tempdir = temp_dir
        except Exception as e:
            # Log a warning but continue; fallback to default tmp if failed
            print(f"Warning: unable to set custom temp directory {temp_dir}: {e}")
    
    # Initialize database
    db = initialize_db(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Initialize system monitoring
    SystemMonitor(app, interval=300)  # Monitor every 5 minutes
    
    # # Create upload directory if it doesn't exist
    # upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'uploads')
    # if not os.path.exists(upload_dir):
    #     os.makedirs(upload_dir)

    # Register blueprints
    from app.routes.auth import auth as auth_blueprint
    from app.routes.files import files as files_blueprint
    from app.routes.admin import admin as admin_blueprint
    from app.routes.api import api as api_blueprint
    
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(files_blueprint)
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(api_blueprint)
    
    # Add template global for datetime functions
    @app.context_processor
    def inject_now() -> dict:
        return {'now': datetime.now}
    
    @app.route('/')
    def index() -> Response:
        return redirect(url_for('auth.login'))
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e: Exception) -> tuple[str, int]:
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e: Exception) -> tuple[str, int]:
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(e: Exception) -> tuple[str, int]:
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(400)
    def bad_request(e: Exception) -> tuple[str, int]:
        return render_template('errors/400.html'), 400
    
    return app 