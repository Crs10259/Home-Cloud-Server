"""
主页面路由模块
处理系统主页、关于页面等基础路由
"""

from flask import Blueprint, render_template, redirect, url_for, jsonify, request, current_app
from flask_login import current_user, login_required
from app.engine import (
    get_resource_engine,
    get_ai_engine,
    get_database_engine,
    get_user_engine,
    User,
    File,
    Folder,
    Activity,
    SystemSetting
)
from config import MainRoutes

main = Blueprint('main', __name__)

@main.route(MainRoutes.INDEX)
def index():
    """主页"""
    if current_user.is_authenticated:
        return redirect(url_for('files.index'))
    else:
        # 获取数据库引擎
        db_engine = get_database_engine()
        if not db_engine:
            return render_template('main/index.html')
        
        # 从系统设置获取站点信息
        site_name = db_engine.get_setting('site_name', 'Home Cloud Server')
        site_description = db_engine.get_setting('site_description', 'Your personal cloud storage solution')
        
        # 获取用户引擎
        user_engine = get_user_engine()
        if not user_engine:
            return render_template('main/index.html',
                                 site_name=site_name,
                                 site_description=site_description)
        
        # 获取基本统计信息
        stats = user_engine.get_system_stats()
        
        return render_template('main/index.html', 
                             site_name=site_name,
                             site_description=site_description,
                             stats=stats)

@main.route(MainRoutes.ABOUT)
def about():
    """关于页面"""
    # 获取数据库引擎
    db_engine = get_database_engine()
    if not db_engine:
        return render_template('main/about.html')
    
    # 从系统设置获取关于信息
    about_content = db_engine.get_setting('about_content', '')
    version = current_app.config.get('VERSION', '1.0.0')
    
    return render_template('main/about.html', 
                         about_content=about_content,
                         version=version)

@main.route(MainRoutes.DASHBOARD)
@login_required
def dashboard():
    """用户仪表盘"""
    # 获取资源引擎
    resource_engine = get_resource_engine()
    if not resource_engine:
        return render_template('main/dashboard.html')
    
    # 获取用户存储使用情况
    storage_info = resource_engine.get_user_storage_info(current_user.id)
    
    # 获取用户活动
    activities = resource_engine.get_user_activities(current_user.id, limit=10)
    
    # 获取文件和文件夹统计
    stats = resource_engine.get_user_resource_stats(current_user.id)
    
    return render_template('main/dashboard.html',
                         storage_info=storage_info,
                         activities=activities,
                         stats=stats)

@main.route(MainRoutes.SEARCH)
@login_required
def search():
    """全局搜索"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return jsonify({'success': False, 'message': '搜索关键词太短'}), 400
    
    # 使用AI引擎进行智能搜索
    ai_engine = get_ai_engine()
    if not ai_engine:
        # 回退到资源引擎的基本搜索
        resource_engine = get_resource_engine()
        if not resource_engine:
            return jsonify({'success': False, 'message': '搜索服务不可用'}), 503
        
        results = resource_engine.basic_search(query, current_user.id)
        return jsonify({'success': True, 'results': results})
    
    # 执行智能搜索
    results = ai_engine.smart_search(query, current_user.id)
    return jsonify({'success': True, 'results': results})

@main.route(MainRoutes.HELP)
def help():
    """帮助页面"""
    # 获取数据库引擎
    db_engine = get_database_engine()
    if not db_engine:
        return render_template('main/help.html')
    
    # 从系统设置获取帮助内容
    help_content = db_engine.get_setting('help_content', '')
    
    return render_template('main/help.html', help_content=help_content) 