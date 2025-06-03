from flask import Flask, render_template, redirect, url_for
import os
from config import config
from app.models.db_init import initialize_db
from datetime import datetime
from app.utils.system_monitor import SystemMonitor
import ssl

def create_app(config_name='default'):
    # Specify the template folder explicitly
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'templates')
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    app.config.from_object(config[config_name])
    
    # Initialize database
    initialize_db(app)
    
    # Initialize system monitoring
    SystemMonitor(app, interval=300)  # Monitor every 5 minutes
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
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
    def inject_now():
        return {'now': datetime.now}
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration
    use_https = app.config.get('USE_HTTPS', False)
    server_port = app.config.get('SERVER_PORT', 5000)
    server_host = app.config.get('SERVER_HOST', '0.0.0.0')
    
    if use_https:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # Paths to certificate and key files (must be configured by user)
        cert_path = os.environ.get('SSL_CERT_PATH', 'cert.pem')
        key_path = os.environ.get('SSL_KEY_PATH', 'key.pem')
        
        if os.path.exists(cert_path) and os.path.exists(key_path):
            context.load_cert_chain(cert_path, key_path)
            app.run(debug=app.config.get('DEBUG', False), 
                    host=server_host, 
                    port=server_port, 
                    ssl_context=context)
        else:
            print("Warning: HTTPS enabled but certificate files not found. Falling back to HTTP.")
            app.run(debug=app.config.get('DEBUG', False), 
                    host=server_host, 
                    port=server_port)
    else:
        app.run(debug=app.config.get('DEBUG', False), 
                host=server_host, 
                port=server_port) 