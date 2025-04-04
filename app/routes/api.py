from flask import Blueprint, request, jsonify, session, g
from app.models.user import db, User
from app.models.file import File, Folder
from app.models.system import SystemMetric, SystemSetting
from functools import wraps
import datetime
import psutil
import os
import uuid
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash

api = Blueprint('api', __name__)

# API authentication
def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or 'Basic ' not in auth_header:
            return jsonify({'error': 'Authentication required'}), 401
        
        try:
            # Extract username and password from header
            encoded_credentials = auth_header.split(' ')[1]
            credentials = encoded_credentials.encode().decode('utf-8')
            username, password = credentials.split(':')
            
            user = User.query.filter_by(username=username).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Store user in g for this request
            g.user = user
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 401
    
    return decorated_function

def api_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or 'Basic ' not in auth_header:
            return jsonify({'error': 'Authentication required'}), 401
        
        try:
            # Extract username and password from header
            encoded_credentials = auth_header.split(' ')[1]
            credentials = encoded_credentials.encode().decode('utf-8')
            username, password = credentials.split(':')
            
            user = User.query.filter_by(username=username).first()
            
            if not user or not check_password_hash(user.password_hash, password):
                return jsonify({'error': 'Invalid credentials'}), 401
            
            # Check if user is admin
            if user.role != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
            
            # Store user in g for this request
            g.user = user
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'error': str(e)}), 401
    
    return decorated_function

# User API endpoints
@api.route('/api/user/info')
@api_login_required
def user_info():
    user = g.user
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'storage_quota': user.storage_quota,
        'storage_used': user.storage_used,
        'storage_percent': user.get_storage_usage_percent(),
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None
    })

# File API endpoints
@api.route('/api/files')
@api_login_required
def list_files():
    user = g.user
    folder_id = request.args.get('folder_id', type=int)
    
    if folder_id:
        folder = Folder.query.filter_by(id=folder_id, user_id=user.id, is_deleted=False).first_or_404()
        files = File.query.filter_by(folder_id=folder_id, user_id=user.id, is_deleted=False).all()
        subfolders = Folder.query.filter_by(parent_id=folder_id, user_id=user.id, is_deleted=False).all()
    else:
        # Get root folder
        folder = Folder.query.filter_by(user_id=user.id, parent_id=None, is_deleted=False).first()
        if not folder:
            return jsonify({'error': 'Root folder not found'}), 404
        
        files = File.query.filter_by(folder_id=folder.id, user_id=user.id, is_deleted=False).all()
        subfolders = Folder.query.filter_by(parent_id=folder.id, user_id=user.id, is_deleted=False).all()
    
    # Convert to dict for JSON response
    folder_dict = folder.to_dict() if folder else None
    files_list = [file.to_dict() for file in files]
    subfolders_list = [subfolder.to_dict() for subfolder in subfolders]
    
    return jsonify({
        'folder': folder_dict,
        'files': files_list,
        'subfolders': subfolders_list
    })

@api.route('/api/folders/create', methods=['POST'])
@api_login_required
def api_create_folder():
    user = g.user
    data = request.json
    
    folder_name = data.get('name')
    parent_id = data.get('parent_id')
    
    if not folder_name:
        return jsonify({'error': 'Folder name is required'}), 400
    
    # Check if folder already exists in the same parent
    existing_folder = Folder.query.filter_by(
        name=folder_name, 
        parent_id=parent_id,
        user_id=user.id,
        is_deleted=False
    ).first()
    
    if existing_folder:
        return jsonify({'error': 'A folder with this name already exists'}), 400
    
    # Create new folder
    new_folder = Folder(
        name=folder_name,
        user_id=user.id,
        parent_id=parent_id
    )
    
    db.session.add(new_folder)
    db.session.commit()
    
    return jsonify({'success': True, 'folder': new_folder.to_dict()})

@api.route('/api/files/upload', methods=['POST'])
@api_login_required
def api_upload_file():
    user = g.user
    folder_id = request.form.get('folder_id', type=int)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    uploaded_file = request.files['file']
    
    if uploaded_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get max upload size from settings
    max_size_setting = SystemSetting.query.filter_by(key='max_upload_size').first()
    max_size = 1024 * 1024 * 1024  # Default 1GB
    if max_size_setting:
        max_size = max_size_setting.get_typed_value()
    
    # Check file size
    uploaded_file.seek(0, os.SEEK_END)
    file_size = uploaded_file.tell()
    uploaded_file.seek(0)
    
    if file_size > max_size:
        return jsonify({'error': 'File too large'}), 400
    
    # Check if user has enough space
    if not user.has_space_for_file(file_size):
        return jsonify({'error': 'Not enough storage space'}), 400
    
    # Save file
    original_filename = secure_filename(uploaded_file.filename)
    
    # Generate unique filename to avoid conflicts
    filename = f"{uuid.uuid4().hex}_{original_filename}"
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'uploads', str(user.id))
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_path = os.path.join(upload_dir, filename)
    uploaded_file.save(file_path)
    
    # Create file record in database
    from app.routes.files import get_file_type
    file_type = get_file_type(original_filename)
    new_file = File(
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        size=file_size,
        file_type=file_type,
        user_id=user.id,
        folder_id=folder_id
    )
    
    db.session.add(new_file)
    db.session.commit()
    
    # Update user's storage usage
    user.storage_used += file_size
    db.session.commit()
    
    return jsonify({'success': True, 'file': new_file.to_dict()})

# Admin API endpoints
@api.route('/api/admin/users')
@api_admin_required
def api_list_users():
    users = User.query.all()
    users_list = []
    
    for user in users:
        users_list.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'storage_quota': user.storage_quota,
            'storage_used': user.storage_used,
            'storage_percent': user.get_storage_usage_percent(),
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None
        })
    
    return jsonify({'users': users_list})

@api.route('/api/admin/system/stats')
@api_admin_required
def api_system_stats():
    # Get real-time system stats
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    net_io_counters = psutil.net_io_counters()
    
    # Record metrics
    new_metric = SystemMetric(
        cpu_usage=cpu_percent,
        memory_usage=memory.percent,
        disk_usage=disk.percent,
        network_rx=net_io_counters.bytes_recv,
        network_tx=net_io_counters.bytes_sent,
        active_connections=len(psutil.net_connections())
    )
    
    db.session.add(new_metric)
    db.session.commit()
    
    return jsonify({
        'cpu': {
            'percent': cpu_percent
        },
        'memory': {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percent': memory.percent
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'free': disk.free,
            'percent': disk.percent
        },
        'network': {
            'bytes_sent': net_io_counters.bytes_sent,
            'bytes_recv': net_io_counters.bytes_recv,
            'packets_sent': net_io_counters.packets_sent,
            'packets_recv': net_io_counters.packets_recv
        },
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@api.route('/api/admin/metrics/history')
@api_admin_required
def api_metrics_history():
    hours = request.args.get('hours', 24, type=int)
    
    # Get metrics for the specified time period
    since = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    metrics = SystemMetric.query.filter(SystemMetric.timestamp >= since).order_by(SystemMetric.timestamp).all()
    
    metrics_list = []
    for metric in metrics:
        metrics_list.append(metric.to_dict())
    
    return jsonify({'metrics': metrics_list}) 