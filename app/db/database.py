import sqlite3
import pathlib
from typing import Optional, List, Dict, Any
import shutil
import logging

logger = logging.getLogger(__name__)
from app.core.config import APP_DATA_DIR, DB_DIR, DATA_DIR

DB_PATH = DB_DIR / "novelvoice.db"

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.conn = None
        return cls._instance

    def connect(self):
        if self.conn is None:
            # 确保目录存在
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # 检查并迁移数据库文件 (v1.3.1+)
            # 优先级: APP_DATA_DIR/novelvoice.db (v1.3.1) > DATA_DIR/novelvoice.db (root v1.3.0)
            migration_sources = [
                APP_DATA_DIR / "novelvoice.db",
                DATA_DIR / "novelvoice.db"
            ]
            
            for old_db_path in migration_sources:
                if old_db_path.exists() and not DB_PATH.exists() and old_db_path != DB_PATH:
                    logger.info(f"📦 检测到旧数据库文件，正在迁移: {old_db_path} -> {DB_PATH}")
                    try:
                        shutil.move(str(old_db_path), str(DB_PATH))
                        logger.info(f"✅ 数据库文件迁移成功: {old_db_path.name}")
                        break # Only migrate one
                    except Exception as e:
                        logger.error(f"❌ 数据库文件迁移失败: {e}")

            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self._init_db()
    
    def _init_db(self):
        cursor = self.conn.cursor()
        # 创建任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                book_name TEXT NOT NULL,
                chapter_index INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                status TEXT DEFAULT 'pending',
                audio_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 创建索引以加速查询
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_book_name ON tasks (book_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks (status)")
        self.conn.commit()
        
        # 尝试迁移旧数据
        try:
            self.migrate_legacy_data()
        except Exception as e:
            logger.warning(f"Migration warning: {e}")

    def delete_book_tasks(self, book_name: str):
        """删除书籍的所有任务记录"""
        if self.conn is None:
            self.connect()
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE book_name = ?", (book_name,))
        self.conn.commit()

    def migrate_legacy_data(self):
        """扫描目录，将现有的 tasks.json 导入数据库"""
        import json
        import re
        
        if not APP_DATA_DIR.exists():
            return

        cursor = self.conn.cursor()
        
        # 扫描目录列表
        search_dirs = []
        if APP_DATA_DIR.exists():
            search_dirs.append(APP_DATA_DIR)
        if DATA_DIR.exists() and DATA_DIR != APP_DATA_DIR:
            search_dirs.append(DATA_DIR)

        for search_dir in search_dirs:
            for book_dir in search_dir.iterdir():
                if book_dir.is_dir() and book_dir.name.endswith("_audio"):
                    # 如果该目录不在 APP_DATA_DIR 中，尝试迁移它
                    target_dir = APP_DATA_DIR / book_dir.name
                    if book_dir.parent != APP_DATA_DIR:
                        if not target_dir.exists():
                            logger.info(f"📦 发现不在 app 子目录的书籍文件夹，正在移动: {book_dir.name}")
                            try:
                                APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
                                shutil.move(str(book_dir), str(target_dir))
                                book_dir = target_dir # 更新指针以进行后续 DB 迁移
                            except Exception as e:
                                logger.error(f"❌ 移动书籍文件夹失败 {book_dir.name}: {e}")
                                continue
                        else:
                            # 目标已存在，跳过此源目录（用户可能手动处理过一部分）
                            continue

                    book_name = book_dir.name.replace("_audio", "").strip()
                tasks_file = book_dir / "tasks.json"
                
                if not tasks_file.exists():
                    continue
                    
                # 检查数据库是否已有记录
                cursor.execute("SELECT 1 FROM tasks WHERE book_name = ? LIMIT 1", (book_name,))
                if cursor.fetchone():
                    continue
                    
                logger.info(f"Migrating legacy tasks for {book_name}...")
                try:
                    with open(tasks_file, 'r', encoding='utf-8') as f:
                        tasks = json.load(f)
                        
                    data_to_insert = []
                    for t in tasks:
                        # 兼容旧数据的 id 及字段
                        # 旧 id 是 int 1, 2, 3...
                        task_id = t.get('id')
                        title = t.get('title', 'Unknown')
                        content = t.get('content', '')
                        status = t.get('status', 'pending')
                        audio_path = t.get('audio_path')
                        
                        data_to_insert.append((
                            f"{book_name}_{task_id}",
                            book_name,
                            task_id,
                            title,
                            content,
                            status,
                            audio_path
                        ))
                    
                    if data_to_insert:
                        cursor.executemany("""
                            INSERT OR IGNORE INTO tasks (id, book_name, chapter_index, title, content, status, audio_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, data_to_insert)
                        self.conn.commit()
                        logger.info(f"Migrated {len(data_to_insert)} tasks for {book_name}")
                        
                        # 可选：重命名 tasks.json 为 tasks.json.bak
                        # tasks_file.rename(tasks_file.with_suffix(".json.bak"))
                        
                except Exception as e:
                    logger.error(f"Failed to migrate {book_name}: {e}")

    def get_cursor(self):
        if self.conn is None:
            self.connect()
        return self.conn.cursor()
    
    def commit(self):
        if self.conn:
            self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

# 全局数据库实例
db = Database()
