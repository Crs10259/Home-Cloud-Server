from flask import session, g, request
from functools import wraps

# Dictionary of available languages
LANGUAGES = {
    'en': 'English',
    'zh': '中文',
    'fr': 'Français',
    'es': 'Español'
}

# Translations dictionary
TRANSLATIONS = {
    'en': {
        # Common UI elements
        'login': 'Login',
        'logout': 'Logout',
        'register': 'Register',
        'profile': 'Profile',
        'settings': 'Settings',
        'admin': 'Admin',
        'dashboard': 'Dashboard',
        'files': 'Files',
        'upload': 'Upload',
        'download': 'Download',
        'delete': 'Delete',
        'share': 'Share',
        'search': 'Search',
        'save': 'Save',
        'cancel': 'Cancel',
        
        # File operations
        'create_folder': 'Create Folder',
        'rename': 'Rename',
        'move': 'Move',
        'copy': 'Copy',
        'size': 'Size',
        'type': 'Type',
        'created': 'Created',
        'modified': 'Modified',
        
        # Alerts and messages
        'success': 'Success',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Information',
        'confirm_delete': 'Are you sure you want to delete this item?',
        'file_uploaded': 'File uploaded successfully',
        'file_deleted': 'File deleted successfully',
        
        # User management
        'username': 'Username',
        'email': 'Email',
        'password': 'Password',
        'confirm_password': 'Confirm Password',
        'role': 'Role',
        'user': 'User',
        'admin': 'Administrator',
        'created_at': 'Created At',
        'last_login': 'Last Login',
        
        # System
        'system_monitoring': 'System Monitoring',
        'cpu_usage': 'CPU Usage',
        'memory_usage': 'Memory Usage',
        'disk_usage': 'Disk Usage',
        'network_traffic': 'Network Traffic',
        'active_connections': 'Active Connections'
    },
    
    'zh': {
        # Common UI elements
        'login': '登录',
        'logout': '登出',
        'register': '注册',
        'profile': '个人资料',
        'settings': '设置',
        'admin': '管理员',
        'dashboard': '仪表盘',
        'files': '文件',
        'upload': '上传',
        'download': '下载',
        'delete': '删除',
        'share': '分享',
        'search': '搜索',
        'save': '保存',
        'cancel': '取消',
        
        # File operations
        'create_folder': '创建文件夹',
        'rename': '重命名',
        'move': '移动',
        'copy': '复制',
        'size': '大小',
        'type': '类型',
        'created': '创建时间',
        'modified': '修改时间',
        
        # Alerts and messages
        'success': '成功',
        'error': '错误',
        'warning': '警告',
        'info': '信息',
        'confirm_delete': '您确定要删除此项目吗？',
        'file_uploaded': '文件上传成功',
        'file_deleted': '文件删除成功',
        
        # User management
        'username': '用户名',
        'email': '电子邮件',
        'password': '密码',
        'confirm_password': '确认密码',
        'role': '角色',
        'user': '用户',
        'admin': '管理员',
        'created_at': '创建时间',
        'last_login': '上次登录',
        
        # System
        'system_monitoring': '系统监控',
        'cpu_usage': 'CPU使用率',
        'memory_usage': '内存使用率',
        'disk_usage': '磁盘使用率',
        'network_traffic': '网络流量',
        'active_connections': '活动连接'
    },
    
    'fr': {
        # Common UI elements
        'login': 'Connexion',
        'logout': 'Déconnexion',
        'register': 'S\'inscrire',
        'profile': 'Profil',
        'settings': 'Paramètres',
        'admin': 'Admin',
        'dashboard': 'Tableau de bord',
        'files': 'Fichiers',
        'upload': 'Télécharger',
        'download': 'Télécharger',
        'delete': 'Supprimer',
        'share': 'Partager',
        'search': 'Rechercher',
        'save': 'Enregistrer',
        'cancel': 'Annuler',
        
        # File operations
        'create_folder': 'Créer un dossier',
        'rename': 'Renommer',
        'move': 'Déplacer',
        'copy': 'Copier',
        'size': 'Taille',
        'type': 'Type',
        'created': 'Créé',
        'modified': 'Modifié',
        
        # Alerts and messages
        'success': 'Succès',
        'error': 'Erreur',
        'warning': 'Avertissement',
        'info': 'Information',
        'confirm_delete': 'Êtes-vous sûr de vouloir supprimer cet élément?',
        'file_uploaded': 'Fichier téléchargé avec succès',
        'file_deleted': 'Fichier supprimé avec succès',
        
        # User management
        'username': 'Nom d\'utilisateur',
        'email': 'E-mail',
        'password': 'Mot de passe',
        'confirm_password': 'Confirmer le mot de passe',
        'role': 'Rôle',
        'user': 'Utilisateur',
        'admin': 'Administrateur',
        'created_at': 'Créé le',
        'last_login': 'Dernière connexion',
        
        # System
        'system_monitoring': 'Surveillance du système',
        'cpu_usage': 'Utilisation du CPU',
        'memory_usage': 'Utilisation de la mémoire',
        'disk_usage': 'Utilisation du disque',
        'network_traffic': 'Trafic réseau',
        'active_connections': 'Connexions actives'
    },
    
    'es': {
        # Common UI elements
        'login': 'Iniciar sesión',
        'logout': 'Cerrar sesión',
        'register': 'Registrarse',
        'profile': 'Perfil',
        'settings': 'Configuración',
        'admin': 'Admin',
        'dashboard': 'Panel de control',
        'files': 'Archivos',
        'upload': 'Subir',
        'download': 'Descargar',
        'delete': 'Eliminar',
        'share': 'Compartir',
        'search': 'Buscar',
        'save': 'Guardar',
        'cancel': 'Cancelar',
        
        # File operations
        'create_folder': 'Crear carpeta',
        'rename': 'Renombrar',
        'move': 'Mover',
        'copy': 'Copiar',
        'size': 'Tamaño',
        'type': 'Tipo',
        'created': 'Creado',
        'modified': 'Modificado',
        
        # Alerts and messages
        'success': 'Éxito',
        'error': 'Error',
        'warning': 'Advertencia',
        'info': 'Información',
        'confirm_delete': '¿Está seguro de que desea eliminar este elemento?',
        'file_uploaded': 'Archivo subido correctamente',
        'file_deleted': 'Archivo eliminado correctamente',
        
        # User management
        'username': 'Nombre de usuario',
        'email': 'Correo electrónico',
        'password': 'Contraseña',
        'confirm_password': 'Confirmar contraseña',
        'role': 'Rol',
        'user': 'Usuario',
        'admin': 'Administrador',
        'created_at': 'Creado el',
        'last_login': 'Último inicio de sesión',
        
        # System
        'system_monitoring': 'Monitoreo del sistema',
        'cpu_usage': 'Uso de CPU',
        'memory_usage': 'Uso de memoria',
        'disk_usage': 'Uso de disco',
        'network_traffic': 'Tráfico de red',
        'active_connections': 'Conexiones activas'
    }
}

def get_translation(key, lang=None):
    """Get a translation for a key in the specified language."""
    if not lang:
        lang = session.get('language_code', 'en')
        if lang not in TRANSLATIONS:
            lang = 'en'
    
    # Extract just the language code from the full name if needed
    if lang in LANGUAGES.values():
        for code, name in LANGUAGES.items():
            if name == lang:
                lang = code
                break
    
    # Get the translation or return the key itself if not found
    return TRANSLATIONS.get(lang, {}).get(key, key)

def init_app(app):
    """Initialize the translation system with the Flask app."""
    
    # Add the translate function to template context
    @app.context_processor
    def inject_translations():
        return {
            't': get_translation,
            'languages': LANGUAGES
        }
    
    # Set language from user preferences or browser request
    @app.before_request
    def set_language():
        # Priority: 1. Session, 2. User preference, 3. Browser Accept-Language, 4. Default (en)
        if 'language' not in session:
            # If user is logged in, use their preference
            user_id = session.get('user_id')
            if user_id:
                from app.models.user import User
                user = User.query.get(user_id)
                if user and user.preferred_language:
                    session['language'] = LANGUAGES.get(user.preferred_language, 'English')
                    session['language_code'] = user.preferred_language
                    return
            
            # Fall back to browser preference
            if request.accept_languages:
                for lang_code, _ in request.accept_languages:
                    if lang_code[:2] in LANGUAGES:
                        session['language'] = LANGUAGES[lang_code[:2]]
                        session['language_code'] = lang_code[:2]
                        return
            
            # Default to English
            session['language'] = 'English'
            session['language_code'] = 'en' 