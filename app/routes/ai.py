from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash, current_app
from flask_login import login_required, current_user
from functools import wraps
import os
import json
import requests
import tempfile
import mimetypes
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from config import AIRoutes
from app.engine import (
    get_ai_engine,
    get_database_engine,
    get_resource_engine,
    SystemSetting,
    User,
    File,
    Activity
)

ai = Blueprint('ai', __name__, url_prefix='/ai')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def is_ai_enabled():
    """Check if AI chat is enabled in system settings"""
    # 获取数据库引擎
    db_engine = get_database_engine()
    if not db_engine:
        return False
    
    # 从系统设置获取AI状态
    return db_engine.get_setting('enable_ai_chat', False)

def get_ai_settings():
    """Get AI settings from the database"""
    settings = {}
    
    # 获取数据库引擎
    db_engine = get_database_engine()
    if not db_engine:
        return settings
    
    # 获取AI设置
    ai_settings = ['ai_provider', 'ai_model', 'ai_api_key']
    
    for key in ai_settings:
        value = db_engine.get_setting(key)
        if value:
            settings[key] = value
    
    # Set defaults for missing settings
    settings.setdefault('ai_provider', 'openai')
    settings.setdefault('ai_model', 'gpt-3.5-turbo')
    
    return settings

@ai.route(AIRoutes.CHAT)
@login_required
def chat():
    """AI聊天界面"""
    # Check if AI chat is enabled
    if not is_ai_enabled():
        flash('AI chat is currently disabled by the administrator', 'warning')
        return redirect(url_for('files.index'))
    
    user_id = current_user.id
    
    # 获取资源引擎
    resource_engine = get_resource_engine()
    if not resource_engine:
        flash('资源服务不可用', 'danger')
        return redirect(url_for('main.index'))
    
    # Get user's files for the file selector
    files = File.query.filter_by(user_id=user_id, is_deleted=False).order_by(File.name).all()
    
    # Get AI settings
    ai_settings = get_ai_settings()
    provider = ai_settings.get('ai_provider')
    model = ai_settings.get('ai_model')
    
    return render_template('ai/chat.html', 
                          user=current_user, 
                          files=files, 
                          provider=provider,
                          model=model)

# Add a decorator to check if AI is enabled for all routes in this blueprint
@ai.before_request
def check_ai_enabled():
    """Check if AI is enabled before processing any AI-related request"""
    # Skip the check for static resources
    if request.endpoint and 'static' in request.endpoint:
        return
        
    # Always allow access to the is_enabled route for status checks
    if request.endpoint == 'ai.is_enabled':
        return
        
    # For all other AI routes, check if AI is enabled
    if not is_ai_enabled():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'AI chat is disabled by administrator'}), 403
        else:
            flash('AI chat is currently disabled by the administrator', 'warning')
            return redirect(url_for('files.index'))

@ai.route(AIRoutes.IS_ENABLED)
@login_required
def is_enabled():
    """检查AI功能是否启用"""
    return jsonify({'enabled': is_ai_enabled()})

@ai.route(AIRoutes.SEND_MESSAGE, methods=['POST'])
@login_required
def send_message():
    """发送消息到AI"""
    if not is_ai_enabled():
        return jsonify({'error': 'AI chat is disabled'}), 400
    
    user_id = current_user.id
    message = request.form.get('message')
    file_id = request.form.get('file_id')
    
    if not message and not file_id:
        return jsonify({'error': 'No message or file provided'}), 400
    
    # Get AI settings
    ai_settings = get_ai_settings()
    provider = ai_settings.get('ai_provider')
    model = ai_settings.get('ai_model')
    api_key = ai_settings.get('ai_api_key')
    
    # 获取资源引擎
    resource_engine = get_resource_engine()
    if not resource_engine:
        return jsonify({'error': '资源服务不可用'}), 503
    
    # 获取数据库引擎
    db_engine = get_database_engine()
    if not db_engine:
        return jsonify({'error': '数据库服务不可用'}), 503
    
    # Prepare file content if a file was sent
    file_content = None
    file_info = None
    
    if file_id:
        try:
            file_id = int(file_id)
            file = File.query.filter_by(id=file_id, user_id=user_id, is_deleted=False).first()
            
            if not file:
                return jsonify({'error': 'File not found'}), 404
            
            # Read file content based on type
            file_content = read_file_content(file)
            
            # Add file info
            file_info = {
                'name': file.name,
                'size': file.size,
                'type': file.mime_type
            }
            
            # Log activity
            db_engine.log_activity(
                user_id=user_id,
                action='ai_analyze',
                details=f"AI分析文件: {file.name}"
            )
            
        except Exception as e:
            current_app.logger.error(f"Error processing file for AI: {e}")
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
    
    # Get AI engine
    ai_engine = get_ai_engine()
    if not ai_engine:
        return jsonify({'error': 'AI服务不可用'}), 503
    
    # Call appropriate AI provider
    try:
        if provider == 'openai':
            response = call_openai(message, file_content, file_info, model, api_key)
        elif provider == 'ollama':
            response = call_ollama(message, file_content, file_info, model)
        elif provider == 'azure':
            response = call_azure_openai(message, file_content, file_info, model, api_key)
        else:
            return jsonify({'error': f'Unknown provider: {provider}'}), 400
        
        return jsonify({'response': response})
        
    except Exception as e:
        current_app.logger.error(f"AI processing error: {e}")
        return jsonify({'error': f'Error processing message: {str(e)}'}), 500

def read_file_content(file):
    """Read file content based on file type"""
    try:
        file_ext = os.path.splitext(file.name)[1].lower()
        
        # Get resource engine to get file path
        resource_engine = get_resource_engine()
        if not resource_engine:
            return "Error: Resource service unavailable"
        
        file_path, _, _, error = resource_engine.download_file(file.id)
        if error:
            return f"Error accessing file: {error}"
        
        # Text files
        if file.mime_type and file.mime_type.startswith('text/') or file_ext in ['.txt', '.md', '.json', '.xml', '.html', '.css', '.js', '.py', '.java', '.c', '.cpp']:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        
        # PDF files - return first N characters to avoid overwhelming the AI
        elif file_ext == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfFileReader(f)
                    text = ""
                    # Get first 10 pages or all pages if less than 10
                    for page_num in range(min(10, pdf_reader.numPages)):
                        text += pdf_reader.getPage(page_num).extractText() + "\n"
                return text[:100000]  # Limit to 100k characters
            except ImportError:
                return "PDF content extraction not available. Please install PyPDF2 package."
        
        # For binary files, just provide info
        else:
            return f"This is a binary file ({file.mime_type}) and its contents cannot be directly displayed."
            
    except Exception as e:
        current_app.logger.error(f"Error reading file content: {e}")
        return f"Error reading file: {str(e)}"

def call_openai(message, file_content, file_info, model, api_key):
    """Call OpenAI API"""
    if not api_key:
        return "Error: OpenAI API key not configured. Please contact administrator."
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare messages
    messages = [{"role": "system", "content": "You are a helpful assistant that analyzes files and answers questions."}]
    
    # If file content is provided, include it
    if file_content and file_info:
        file_prompt = f"Here is the content of the file '{file_info['name']}' ({file_info['type']}, {file_info['size']} bytes):\n\n{file_content}"
        messages.append({"role": "user", "content": file_prompt})
    
    # Add user message
    messages.append({"role": "user", "content": message})
    
    # Make API call
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": messages,
                "max_tokens": 2000
            }
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            current_app.logger.error(f"OpenAI error: {response.text}")
            return f"Error from OpenAI API: {response.status_code} - {response.text}"
    
    except Exception as e:
        current_app.logger.error(f"Error calling OpenAI: {e}")
        return f"Error calling OpenAI: {str(e)}"

def call_ollama(message, file_content, file_info, model):
    """Call Ollama local API"""
    headers = {
        "Content-Type": "application/json"
    }
    
    # Prepare prompt
    prompt = ""
    
    # If file content is provided, include it
    if file_content and file_info:
        prompt += f"Here is the content of the file '{file_info['name']}' ({file_info['type']}, {file_info['size']} bytes):\n\n{file_content}\n\n"
    
    # Add user message
    prompt += message
    
    # Make API call
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            headers=headers,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            return response.json().get("response", "No response from Ollama")
        else:
            current_app.logger.error(f"Ollama error: {response.text}")
            return f"Error from Ollama API: {response.status_code} - {response.text}"
    
    except Exception as e:
        current_app.logger.error(f"Error calling Ollama: {e}")
        return f"Error calling Ollama: {str(e)}. Make sure Ollama is running on localhost:11434."

def call_azure_openai(message, file_content, file_info, model, api_key):
    """Call Azure OpenAI API"""
    if not api_key:
        return "Error: Azure OpenAI API key not configured. Please contact administrator."
    
    # Get database engine to fetch Azure endpoint
    db_engine = get_database_engine()
    if not db_engine:
        return "Error: Database service unavailable"
    
    # Azure requires separate endpoint setting
    endpoint = db_engine.get_setting('azure_endpoint')
    if not endpoint:
        return "Error: Azure OpenAI endpoint not configured. Please contact administrator."
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    # Prepare messages
    messages = [{"role": "system", "content": "You are a helpful assistant that analyzes files and answers questions."}]
    
    # If file content is provided, include it
    if file_content and file_info:
        file_prompt = f"Here is the content of the file '{file_info['name']}' ({file_info['type']}, {file_info['size']} bytes):\n\n{file_content}"
        messages.append({"role": "user", "content": file_prompt})
    
    # Add user message
    messages.append({"role": "user", "content": message})
    
    # Make API call
    try:
        response = requests.post(
            f"{endpoint}/openai/deployments/{model}/chat/completions?api-version=2023-05-15",
            headers=headers,
            json={
                "messages": messages,
                "max_tokens": 2000
            }
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            current_app.logger.error(f"Azure OpenAI error: {response.text}")
            return f"Error from Azure OpenAI API: {response.status_code} - {response.text}"
    
    except Exception as e:
        current_app.logger.error(f"Error calling Azure OpenAI: {e}")
        return f"Error calling Azure OpenAI: {str(e)}"