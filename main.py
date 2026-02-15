import os
import ssl
from app import create_app
import platform
from pathlib import Path

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration
    use_https = app.config.get('USE_HTTPS', False)
    server_port = app.config.get('SERVER_PORT', 5000)
    server_host = app.config.get('SERVER_HOST', '0.0.0.0')
    
    if use_https:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # Get certificate paths based on operating system
        system = platform.system().lower()
        if system == 'windows':
            ssl_dir = Path(app.root_path).parent / 'ssl'
            ssl_dir.mkdir(parents=True, exist_ok=True)
            cert_path = str(ssl_dir / 'home-cloud.crt')
            key_path = str(ssl_dir / 'home-cloud.key')
        else:  # Linux/Unix systems
            cert_path = '/etc/ssl/certs/home-cloud.crt'
            key_path = '/etc/ssl/private/home-cloud.key'

        # Override with config if provided
        cert_path = app.config.get('SSL_CERT', cert_path)
        key_path = app.config.get('SSL_KEY', key_path)

        # Check if certificate files exist
        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            print(f"Warning: SSL certificate files not found at {cert_path} and {key_path}")
            print("Running without HTTPS. Please configure SSL certificates for secure operation.")
            app.run(debug=app.config.get('DEBUG', False), 
                    host=server_host, 
                    port=server_port)
        else:
            try:
                context.load_cert_chain(cert_path, key_path)
                app.ssl_context = context
                app.run(debug=app.config.get('DEBUG', False), 
                        host=server_host, 
                        port=server_port, 
                        ssl_context=context)
            except Exception as e:
                print(f"Error loading SSL certificates: {e}")
                print("Running without HTTPS. Please check your SSL configuration.")
                app.run(debug=app.config.get('DEBUG', False), 
                        host=server_host, 
                        port=server_port)
    else:
        app.run(debug=app.config.get('DEBUG', False), 
                host=server_host, 
                port=server_port) 