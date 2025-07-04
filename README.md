# Home Cloud Server

A powerful personal cloud storage server with features for file upload, download, preview, and management.

## Features

- 🔒 Secure HTTPS access
- 📁 File upload and management
- 🗑️ Trash bin functionality
- 📊 Transfer rate monitoring
- 📱 Responsive design for mobile access
- 🔍 File preview support
- 📂 Folder upload support
- ⚡ HTTP/2 support
- 🔄 Automatic startup and system service integration

## System Requirements

- Python 3.8+
- Nginx
- SQLite3
- Linux or Windows operating system

## Installation Guide

### 1. Clone Repository

```bash
git clone https://github.com/Crs10259/Home-Cloud-Server.git
cd Home-Cloud-Server
```

### 2. Create Virtual Environment

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Storage Path

#### Windows
Default storage path is `D:\cloud_storage`, containing:
- uploads: File upload directory
- home-cloud: Database directory
- trash: Recycle bin directory
- temp: Temporary file directory

#### Linux
Default storage path is `/mnt/cloud_storage` or `~/cloud_storage`, with the same directory structure.

### 5. Configure SSL Certificate

#### Using Self-Signed Certificate
```bash
# Linux
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:4096 \
    -keyout /etc/ssl/private/home-cloud.key \
    -out /etc/ssl/certs/home-cloud.crt \
    -subj "/CN=your_domain_or_ip"

# Windows
# SSL certificates will be stored in the ssl folder within the project directory
```

#### Using Let's Encrypt Certificate (Recommended for Public Access)
Requires domain configuration and certbot installation.

### 6. Configure Nginx

```nginx
server {
    listen 80;
    server_name your_domain_or_ip;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your_domain_or_ip;
    client_max_body_size 2000M;

    ssl_certificate /path/to/cert.crt;
    ssl_certificate_key /path/to/cert.key;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/static/;
        expires 30d;
    }
}
```

### 7. Set Up System Service (Linux)

```bash
sudo nano /etc/systemd/system/home-cloud.service
```

```ini
[Unit]
Description=Home Cloud Server
After=network.target

[Service]
User=your_username
Group=your_username
WorkingDirectory=/path/to/Home-Cloud-Server
Environment="PATH=/path/to/Home-Cloud-Server/venv/bin"
ExecStart=/path/to/Home-Cloud-Server/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable home-cloud
sudo systemctl start home-cloud
```

## Configuration

### Environment Variables

- `FLASK_ENV`: Set environment (development/production)
- `SECRET_KEY`: Flask secret key
- `SERVER_PORT`: Server port (default 5000)
- `SERVER_HOST`: Server host (default 0.0.0.0)
- `USE_HTTPS`: Enable HTTPS (default True)

### Storage Configuration

The `config.py` file automatically detects the operating system and uses appropriate paths:

- Windows: `D:\cloud_storage`
- Linux: `/mnt/cloud_storage` or `~/cloud_storage`

### Supported File Types

The system supports:
- Documents: txt, pdf, doc, docx, md
- Images: png, jpg, jpeg, gif
- Media: mp4, mp3
- Office: xls, xlsx
- Archives: zip, rar
- Development: py, js, css, html, json, xml

## Development Guide

### Directory Structure

```
Home-Cloud-Server/
├── app/
│   ├── static/
│   ├── templates/
│   ├── models/
│   ├── routes/
│   └── utils/
├── venv/
├── config.py
├── app.py
└── requirements.txt
```

### Running Development Server

```bash
# Set development environment
export FLASK_ENV=development  # Linux/macOS
set FLASK_ENV=development    # Windows

# Run server
python app.py
```

## Security Recommendations

1. Use strong passwords for admin interface
2. Regularly backup data
3. Keep system and dependencies updated
4. Use trusted SSL certificates for public access
5. Configure firewall to only allow necessary ports

## Troubleshooting

1. Permission Issues
   - Check storage directory permissions
   - Verify SSL certificate permissions

2. Service Won't Start
   - Check port availability
   - Review log files
   - Verify Python environment

3. Upload Failures
   - Check directory permissions
   - Verify file size limits
   - Check disk space

## Contributing

1. Fork the project
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[MIT License](LICENSE)
