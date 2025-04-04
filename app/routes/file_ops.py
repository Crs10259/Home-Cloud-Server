from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.file import File
from app.models.folder import Folder
from app.models.activity import Activity
from app.models.system_setting import SystemSetting
from app.extensions import db
import os
import mimetypes

file_ops = Blueprint('file_ops', __name__)

@file_ops.route('/')
@login_required
def index():
    """List files and folders in the current directory."""
    folder_id = request.args.get('folder_id', None)
    
    if folder_id:
        current_folder = Folder.query.get_or_404(folder_id)
        if current_folder.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
    else:
        current_folder = Folder.query.filter_by(user_id=current_user.id, parent_id=None).first()
    
    folders = Folder.query.filter_by(parent_id=current_folder.id if current_folder else None).all()
    files = File.query.filter_by(folder_id=current_folder.id if current_folder else None).all()
    
    return render_template('files/index.html', 
                         current_folder=current_folder,
                         folders=folders,
                         files=files)

@file_ops.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload."""
    folder_id = request.form.get('folder_id')
    folder = Folder.query.get_or_404(folder_id)
    
    if folder.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Check file size limit
    max_size_setting = SystemSetting.query.filter_by(key='max_upload_size').first()
    max_size = int(max_size_setting.value) if max_size_setting else 1024 * 1024 * 1024  # Default 1GB
    
    if file.content_length > max_size:
        return jsonify({'error': 'File too large'}), 400
    
    # Check user quota
    if current_user.storage_used + file.content_length > current_user.storage_quota:
        return jsonify({'error': 'Storage quota exceeded'}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                            str(current_user.id), 
                            str(folder.id), 
                            filename)
    
    # Create user and folder directories if they don't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Save file
    file.save(file_path)
    
    # Create file record
    new_file = File(
        name=filename,
        path=file_path,
        size=os.path.getsize(file_path),
        mime_type=mimetypes.guess_type(filename)[0],
        user_id=current_user.id,
        folder_id=folder.id
    )
    
    # Update user's storage usage
    current_user.storage_used += new_file.size
    
    # Record activity
    activity = Activity(
        user_id=current_user.id,
        action='upload',
        target=filename,
        details=f'Uploaded file to folder {folder.name}'
    )
    
    db.session.add(new_file)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'message': 'File uploaded successfully'})

@file_ops.route('/download/<int:file_id>')
@login_required
def download_file(file_id):
    """Download a file."""
    file = File.query.get_or_404(file_id)
    
    if file.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    # Record activity
    activity = Activity(
        user_id=current_user.id,
        action='download',
        target=file.name,
        details=f'Downloaded file from folder {file.folder.name}'
    )
    db.session.add(activity)
    db.session.commit()
    
    return send_file(file.path, as_attachment=True)

@file_ops.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    """Create a new folder."""
    parent_id = request.form.get('parent_id')
    folder_name = request.form.get('name')
    
    if not folder_name:
        return jsonify({'error': 'Folder name is required'}), 400
    
    if parent_id:
        parent = Folder.query.get_or_404(parent_id)
        if parent.user_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        path = os.path.join(parent.path, folder_name)
    else:
        path = os.path.join('/', folder_name)
    
    new_folder = Folder(
        name=folder_name,
        path=path,
        user_id=current_user.id,
        parent_id=parent_id
    )
    
    # Record activity
    activity = Activity(
        user_id=current_user.id,
        action='create_folder',
        target=folder_name,
        details=f'Created new folder'
    )
    
    db.session.add(new_folder)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({'message': 'Folder created successfully'})

@file_ops.route('/delete/<string:item_type>/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_type, item_id):
    """Delete a file or folder."""
    if item_type == 'file':
        item = File.query.get_or_404(item_id)
    elif item_type == 'folder':
        item = Folder.query.get_or_404(item_id)
    else:
        return jsonify({'error': 'Invalid item type'}), 400
    
    if item.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    if item_type == 'file':
        # Update user's storage usage
        current_user.storage_used -= item.size
        # Delete physical file
        try:
            os.remove(item.path)
        except OSError:
            pass  # File might not exist
    else:
        # Delete all files in the folder
        files = File.query.filter_by(folder_id=item.id).all()
        for file in files:
            current_user.storage_used -= file.size
            try:
                os.remove(file.path)
            except OSError:
                pass
    
    # Record activity
    activity = Activity(
        user_id=current_user.id,
        action=f'delete_{item_type}',
        target=item.name,
        details=f'Deleted {item_type}'
    )
    
    db.session.add(activity)
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': f'{item_type.capitalize()} deleted successfully'}) 