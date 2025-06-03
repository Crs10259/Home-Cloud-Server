"""
下载路由模块
处理文件下载相关的请求
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from config import APIRoutes
from app.engine.transfer import download_engine

# 创建蓝图
download = Blueprint('download', __name__)

@download.route(APIRoutes.DOWNLOAD_TASKS)
@login_required
def get_download_tasks():
    """获取下载任务列表"""
    tasks = download_engine.get_user_tasks(current_user.id)
    return jsonify({
        'status': 'success',
        'tasks': [task.to_dict() for task in tasks]
    })

@download.route(APIRoutes.DOWNLOADS_CREATE, methods=['POST'])
@login_required
def create_download_task():
    """创建下载任务"""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({
            'status': 'error',
            'message': '缺少必要参数'
        }), 400
    
    url = data['url']
    filename = data.get('filename')
    if not filename:
        filename = secure_filename(os.path.basename(url))
    
    task = download_engine.create_task(
        user_id=current_user.id,
        url=url,
        filename=filename
    )
    
    return jsonify({
        'status': 'success',
        'task': task.to_dict()
    })

@download.route(APIRoutes.DOWNLOAD_TASK)
@login_required
def get_download_task(task_id):
    """获取下载任务详情"""
    task = download_engine.get_task(task_id)
    if not task or task.user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': '任务不存在'
        }), 404
    
    return jsonify({
        'status': 'success',
        'task': task.to_dict()
    })

@download.route(APIRoutes.DOWNLOAD_ACTION, methods=['POST'])
@login_required
def download_action(task_id, action):
    """执行下载任务操作"""
    task = download_engine.get_task(task_id)
    if not task or task.user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': '任务不存在'
        }), 404
    
    if action == 'pause':
        download_engine.pause_task(task_id)
    elif action == 'resume':
        download_engine.resume_task(task_id)
    elif action == 'cancel':
        download_engine.cancel_task(task_id)
    else:
        return jsonify({
            'status': 'error',
            'message': '不支持的操作'
        }), 400
    
    return jsonify({
        'status': 'success',
        'message': '操作成功'
    })

@download.route(APIRoutes.FILE_DOWNLOAD)
@login_required
def download_file(file_id):
    """下载文件"""
    file = download_engine.get_file(file_id)
    if not file or file.user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': '文件不存在'
        }), 404
    
    file_path = os.path.join(current_app.config['DOWNLOAD_FOLDER'], file.filename)
    if not os.path.exists(file_path):
        return jsonify({
            'status': 'error',
            'message': '文件不存在'
        }), 404
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file.filename
    ) 