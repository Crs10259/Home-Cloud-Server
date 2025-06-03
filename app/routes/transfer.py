"""
传输路由模块
处理文件上传和下载的传输任务
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, g
from flask_login import login_required, current_user
from app.engine import (
    get_transfer_engine,  
    get_resource_engine
)
from config import TransferRoutes

transfer = Blueprint('transfer', __name__, url_prefix='/transfer')

@transfer.route(TransferRoutes.PREFIX)
@login_required
def index():
    """传输中心主页"""
    # 获取传输引擎
    transfer_engine = get_transfer_engine()
    if not transfer_engine:
        flash('传输服务不可用', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取活动的传输任务
    active_tasks = transfer_engine.get_active_tasks(current_user.id)
    completed_tasks = transfer_engine.get_completed_tasks(current_user.id, limit=10)
    failed_tasks = transfer_engine.get_failed_tasks(current_user.id, limit=10)
    
    return render_template('transfer/index.html',
                         active_tasks=active_tasks,
                         completed_tasks=completed_tasks,
                         failed_tasks=failed_tasks)

@transfer.route(TransferRoutes.HISTORY)
@login_required
def tasks():
    """传输任务列表"""
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 获取传输引擎
    transfer_engine = get_transfer_engine()
    if not transfer_engine:
        flash('传输服务不可用', 'danger')
        return redirect(url_for('transfer.index'))
    
    # 获取任务列表
    tasks = transfer_engine.get_tasks(
        user_id=current_user.id,
        status=status,
        page=page,
        per_page=per_page
    )
    
    return render_template('transfer/tasks.html', tasks=tasks)

@transfer.route(TransferRoutes.CREATE_TASK, methods=['POST'])
@login_required
def create_task():
    """创建传输任务"""
    task_type = request.form.get('type')  # 'upload' or 'download'
    url = request.form.get('url')
    file = request.files.get('file')
    
    if task_type not in ['upload', 'download']:
        return jsonify({'error': '无效的任务类型'}), 400
    
    if task_type == 'download' and not url:
        return jsonify({'error': '下载URL不能为空'}), 400
    
    if task_type == 'upload' and not file:
        return jsonify({'error': '未选择上传文件'}), 400
    
    # 获取传输引擎
    transfer_engine = get_transfer_engine()
    if not transfer_engine:
        return jsonify({'error': '传输服务不可用'}), 503
    
    # 创建任务
    if task_type == 'download':
        task = transfer_engine.create_download_task(current_user.id, url)
    else:
        task = transfer_engine.create_upload_task(current_user.id, file)
    
    if not task:
        return jsonify({'error': '创建任务失败'}), 500
    
    return jsonify({
        'success': True,
        'task': task.to_dict()
    })

@transfer.route(TransferRoutes.CANCEL_TASK, methods=['POST'])
@login_required
def task_action(task_id):
    """任务操作（暂停、恢复、取消）"""
    action = request.form.get('action')
    if action not in ['pause', 'resume', 'cancel']:
        return jsonify({'error': '无效的操作'}), 400
    
    # 获取传输引擎
    transfer_engine = get_transfer_engine()
    if not transfer_engine:
        return jsonify({'error': '传输服务不可用'}), 503
    
    # 执行操作
    success = False
    if action == 'pause':
        success = transfer_engine.pause_task(task_id, current_user.id)
    elif action == 'resume':
        success = transfer_engine.resume_task(task_id, current_user.id)
    else:  # cancel
        success = transfer_engine.cancel_task(task_id, current_user.id)
    
    if not success:
        return jsonify({'error': f'任务{action}失败'}), 500
    
    return jsonify({'success': True})

@transfer.route(TransferRoutes.PROGRESS)
@login_required
def task_detail(task_id):
    """任务详情"""
    # 获取传输引擎
    transfer_engine = get_transfer_engine()
    if not transfer_engine:
        flash('传输服务不可用', 'danger')
        return redirect(url_for('transfer.tasks'))
    
    # 获取任务信息
    task = transfer_engine.get_task(task_id, current_user.id)
    if not task:
        flash('任务不存在', 'danger')
        return redirect(url_for('transfer.tasks'))
    
    return render_template('transfer/task_detail.html', task=task)

@transfer.route(TransferRoutes.SETTINGS, methods=['GET', 'POST'])
@login_required
def settings():
    """传输设置"""
    # 获取传输引擎
    transfer_engine = get_transfer_engine()
    if not transfer_engine:
        flash('传输服务不可用', 'danger')
        return redirect(url_for('transfer.index'))
    
    if request.method == 'POST':
        # 更新设置
        settings = {
            'max_upload_speed': request.form.get('max_upload_speed', type=int),
            'max_download_speed': request.form.get('max_download_speed', type=int),
            'concurrent_tasks': request.form.get('concurrent_tasks', type=int),
            'auto_retry': request.form.get('auto_retry') == 'on',
            'retry_count': request.form.get('retry_count', type=int)
        }
        
        success = transfer_engine.update_user_settings(current_user.id, settings)
        if success:
            flash('设置已更新', 'success')
        else:
            flash('更新设置失败', 'danger')
    
    # 获取当前设置
    current_settings = transfer_engine.get_user_settings(current_user.id)
    
    return render_template('transfer/settings.html', settings=current_settings) 