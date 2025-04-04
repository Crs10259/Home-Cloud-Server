import sqlite3
import os
import uuid
from config import config
from datetime import datetime, timedelta

def migrate_database():
    # Get the database path from config
    db_path = os.environ.get('DATABASE_URL') or os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dev.db')
    
    # Strip sqlite:/// prefix if it exists
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]
    
    print(f"正在迁移数据库: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查 users 表的列
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in cursor.fetchall()]
    
    # 添加 trash_retention_days 列并移除 preferred_language 列
    if 'trash_retention_days' not in user_columns:
        print("添加 trash_retention_days 列到 users 表...")
        cursor.execute("ALTER TABLE users ADD COLUMN trash_retention_days INTEGER DEFAULT 30")
        conn.commit()
        print("添加成功。")
    else:
        print("trash_retention_days 列已存在。")
    
    # 检查 files 表的列
    cursor.execute("PRAGMA table_info(files)")
    file_columns = [col[1] for col in cursor.fetchall()]
    
    # 添加回收站相关列到 files 表
    if 'deleted_at' not in file_columns:
        print("添加 deleted_at 列到 files 表...")
        cursor.execute("ALTER TABLE files ADD COLUMN deleted_at TIMESTAMP")
        conn.commit()
        print("添加成功。")
    else:
        print("deleted_at 列已存在。")
    
    if 'expiry_date' not in file_columns:
        print("添加 expiry_date 列到 files 表...")
        cursor.execute("ALTER TABLE files ADD COLUMN expiry_date TIMESTAMP")
        conn.commit()
        print("添加成功。")
    
    # 检查 folders 表的列
    cursor.execute("PRAGMA table_info(folders)")
    folder_columns = [col[1] for col in cursor.fetchall()]
    
    # 添加回收站相关列到 folders 表
    if 'deleted_at' not in folder_columns:
        print("添加 deleted_at 列到 folders 表...")
        cursor.execute("ALTER TABLE folders ADD COLUMN deleted_at TIMESTAMP")
        conn.commit()
        print("添加成功。")
    else:
        print("deleted_at 列已存在。")
    
    if 'expiry_date' not in folder_columns:
        print("添加 expiry_date 列到 folders 表...")
        cursor.execute("ALTER TABLE folders ADD COLUMN expiry_date TIMESTAMP")
        conn.commit()
        print("添加成功。")
    
    # 检查 file_activities 表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='file_activities'")
    if not cursor.fetchone():
        print("创建 file_activities 表...")
        cursor.execute('''
            CREATE TABLE file_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                file_id INTEGER,
                folder_id INTEGER,
                activity_type VARCHAR(20) NOT NULL,
                details TEXT,
                file_name VARCHAR(255),
                file_size BIGINT,
                file_type VARCHAR(50),
                duration INTEGER,
                speed FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (file_id) REFERENCES files(id),
                FOREIGN KEY (folder_id) REFERENCES folders(id)
            )
        ''')
        conn.commit()
        print("创建成功。")
    else:
        print("file_activities 表已存在。")
    
    # Add missing columns to activities table
    print("检查activities表是否存在...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
    if cursor.fetchone():
        print("检查activities表是否需要添加传输相关字段...")
        cursor.execute("PRAGMA table_info(activities)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'file_size' not in columns:
            print("添加file_size字段...")
            cursor.execute('ALTER TABLE activities ADD COLUMN file_size BIGINT')
        
        if 'duration' not in columns:
            print("添加duration字段...")
            cursor.execute('ALTER TABLE activities ADD COLUMN duration FLOAT')
        
        if 'transfer_speed' not in columns:
            print("添加transfer_speed字段...")
            cursor.execute('ALTER TABLE activities ADD COLUMN transfer_speed FLOAT')
        
        if 'file_type' not in columns:
            print("添加file_type字段...")
            cursor.execute('ALTER TABLE activities ADD COLUMN file_type VARCHAR(50)')
    else:
        print("activities表不存在，创建表...")
        cursor.execute('''
            CREATE TABLE activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action VARCHAR(64) NOT NULL,
                target VARCHAR(255),
                details TEXT,
                ip_address VARCHAR(50),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                file_size BIGINT,
                duration FLOAT,
                transfer_speed FLOAT,
                file_type VARCHAR(50),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        print("创建activities表成功。")
    
    # Add missing columns to files table
    print("检查files表是否需要添加回收站相关字段...")
    cursor.execute("PRAGMA table_info(files)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'deleted_at' not in columns:
        print("添加deleted_at字段...")
        cursor.execute('ALTER TABLE files ADD COLUMN deleted_at DATETIME')
    
    if 'expiry_date' not in columns:
        print("添加expiry_date字段...")
        cursor.execute('ALTER TABLE files ADD COLUMN expiry_date DATETIME')
    
    # Add missing columns to folders table
    print("检查folders表是否需要添加回收站相关字段...")
    cursor.execute("PRAGMA table_info(folders)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'deleted_at' not in columns:
        print("添加deleted_at字段...")
        cursor.execute('ALTER TABLE folders ADD COLUMN deleted_at DATETIME')
    
    if 'expiry_date' not in columns:
        print("添加expiry_date字段...")
        cursor.execute('ALTER TABLE folders ADD COLUMN expiry_date DATETIME')
    
    # Check if trash settings exist
    print("检查回收站相关系统设置是否存在...")
    cursor.execute("SELECT COUNT(*) FROM system_settings WHERE key='default_trash_retention_days'")
    
    if not cursor.fetchone()[0]:
        print("添加回收站相关系统设置...")
        
        # Default trash retention days
        cursor.execute('''
            INSERT INTO system_settings (key, value, value_type, description, is_advanced)
            VALUES ('default_trash_retention_days', '30', 'integer', '回收站文件默认保留天数', 0)
        ''')
        
        # Enable trash
        cursor.execute('''
            INSERT INTO system_settings (key, value, value_type, description, is_advanced)
            VALUES ('enable_trash', 'true', 'boolean', '启用回收站功能', 0)
        ''')
        
        # Auto clean trash
        cursor.execute('''
            INSERT INTO system_settings (key, value, value_type, description, is_advanced)
            VALUES ('auto_clean_trash', 'true', 'boolean', '自动清理过期回收站文件', 0)
        ''')
        
        conn.commit()
        print("添加成功。")
    else:
        print("回收站相关系统设置已存在。")
    
    # Add server configuration settings
    print("检查服务器配置相关系统设置是否存在...")
    cursor.execute("SELECT COUNT(*) FROM system_settings WHERE key='use_https'")
    
    if not cursor.fetchone()[0]:
        print("添加服务器配置相关系统设置...")
        
        # HTTPS setting
        cursor.execute('''
            INSERT INTO system_settings (key, value, value_type, description, is_advanced)
            VALUES ('use_https', 'false', 'boolean', '使用HTTPS协议', 1)
        ''')
        
        # Server port
        cursor.execute('''
            INSERT INTO system_settings (key, value, value_type, description, is_advanced)
            VALUES ('server_port', '5000', 'integer', '服务器端口号', 1)
        ''')
        
        # Server host
        cursor.execute('''
            INSERT INTO system_settings (key, value, value_type, description, is_advanced)
            VALUES ('server_host', '0.0.0.0', 'string', '服务器主机地址', 1)
        ''')
        
        # Monitor transfer speed
        cursor.execute('''
            INSERT INTO system_settings (key, value, value_type, description, is_advanced)
            VALUES ('monitor_transfer_speed', 'true', 'boolean', '监控文件传输速度', 0)
        ''')
        
        # Allow folder upload
        cursor.execute('''
            INSERT INTO system_settings (key, value, value_type, description, is_advanced)
            VALUES ('allow_folder_upload', 'true', 'boolean', '允许文件夹上传', 0)
        ''')
        
        conn.commit()
        print("添加成功。")
    else:
        print("服务器配置相关系统设置已存在。")
    
    # 关闭连接
    conn.close()
    print("迁移完成。")

if __name__ == "__main__":
    migrate_database() 