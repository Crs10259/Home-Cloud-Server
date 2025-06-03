"""
用户路由模块
处理用户相关功能
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g
from flask_login import login_required, current_user
from app.engine import (
    get_transfer_engine,
    get_user_engine,
    get_resource_engine
)
from config import UserRoutes

user = Blueprint('user', __name__, url_prefix='/user')

@user.route(UserRoutes.PROFILE)
@login_required
def profile():
    """用户个人资料页面"""
    # 获取资源引擎
    resource_engine = get_resource_engine()
    if not resource_engine:
        flash('资源服务不可用', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取用户统计信息
    stats = resource_engine.get_user_resource_stats(current_user.id)
    
    # 获取最近活动
    activities = resource_engine.get_user_activities(current_user.id, limit=10)
    
    return render_template(
        'user/profile.html',
        user=current_user,
        stats=stats,
        activities=activities
    )

@user.route(UserRoutes.SETTINGS)
@login_required
def settings():
    """用户设置页面"""
    # 获取用户引擎
    user_engine = get_user_engine()
    if not user_engine:
        flash('用户服务不可用', 'danger')
        return redirect(url_for('main.index'))
    
    # 获取用户设置
    settings = user_engine.get_user_settings(current_user.id)
    
    return render_template('user/settings.html', 
                         user=current_user,
                         settings=settings)

@user.route(UserRoutes.ACTIVITIES)
@login_required
def activities():
    """用户活动记录页面"""
    # 获取资源引擎
    resource_engine = get_resource_engine()
    if not resource_engine:
        flash('资源服务不可用', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 获取用户活动
    activities = resource_engine.get_user_activities(
        current_user.id,
        page=page,
        per_page=per_page
    )
    
    return render_template('user/activities.html', activities=activities)

@user.route(UserRoutes.DOWNLOADS)
@login_required
def downloads():
    """用户下载记录页面"""
    # 获取下载引擎
    transfer_engine = get_transfer_engine()
    if not transfer_engine:
        flash('下载服务不可用', 'danger')
        return redirect(url_for('main.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 获取下载历史
    downloads = transfer_engine.get_user_download_history(
        current_user.id,
        page=page,
        per_page=per_page
    )
    
    return render_template('user/downloads.html', downloads=downloads)

@user.route(UserRoutes.SECURITY, methods=['GET', 'POST'])
@login_required
def security():
    """安全设置页面"""
    # 获取用户引擎
    user_engine = get_user_engine()
    if not user_engine:
        flash('用户服务不可用', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # 更新安全设置
        data = {
            'enable_2fa': request.form.get('enable_2fa') == 'on',
            'current_password': request.form.get('current_password'),
            'new_password': request.form.get('new_password')
        }
        success, message = user_engine.update_security_settings(current_user.id, data)
        if success:
            flash('安全设置已更新', 'success')
        else:
            flash(message, 'danger')
    
    # 获取安全设置
    security_settings = user_engine.get_security_settings(current_user.id)
    
    return render_template('user/security.html', 
                         user=current_user,
                         security=security_settings)

@user.route(UserRoutes.API_KEYS, methods=['GET', 'POST'])
@login_required
def api_keys():
    """API密钥管理页面"""
    # 获取用户引擎
    user_engine = get_user_engine()
    if not user_engine:
        flash('用户服务不可用', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            # 创建新的API密钥
            name = request.form.get('name')
            success, result = user_engine.create_api_key(current_user.id, name)
            if success:
                flash('API密钥已创建', 'success')
            else:
                flash(result, 'danger')
        elif action == 'delete':
            # 删除API密钥
            key_id = request.form.get('key_id')
            success, message = user_engine.delete_api_key(current_user.id, key_id)
            if success:
                flash('API密钥已删除', 'success')
            else:
                flash(message, 'danger')
    
    # 获取API密钥列表
    api_keys = user_engine.get_api_keys(current_user.id)
    
    return render_template('user/api_keys.html', 
                         user=current_user,
                         api_keys=api_keys) 