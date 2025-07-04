import os
import ssl
from app import create_app

if __name__ == '__main__':
    app = create_app()
    
    # Get configuration
    use_https = app.config.get('USE_HTTPS', False)
    server_port = app.config.get('SERVER_PORT', 5000)
    server_host = app.config.get('SERVER_HOST', '0.0.0.0')
    
    if use_https:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # Get certificate paths from config
        cert_path = app.config.get('SSL_CERT', '/etc/ssl/certs/home-cloud.crt')
        key_path = app.config.get('SSL_KEY', '/etc/ssl/private/home-cloud.key')
        
        if os.path.exists(cert_path) and os.path.exists(key_path):
            context.load_cert_chain(cert_path, key_path)
            app.run(debug=app.config.get('DEBUG', False), 
                    host=server_host, 
                    port=server_port, 
                    ssl_context=context)
        else:
            print(f"Warning: HTTPS enabled but certificate files not found at {cert_path} and {key_path}. Falling back to HTTP.")
            app.run(debug=app.config.get('DEBUG', False), 
                    host=server_host, 
                    port=server_port)
    else:
        app.run(debug=app.config.get('DEBUG', False), 
                host=server_host, 
                port=server_port) 