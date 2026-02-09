import os
import re
import json
import shutil
import pathlib
import shutil
import pathlib
from typing import List, Dict, Any
from .parsers import ParserFactory
import logging

logger = logging.getLogger(__name__)

class BookProcessor:
    def __init__(self, file_path: str):
        self.file_path = pathlib.Path(file_path)
        self.filename = self.file_path.name
        self.book_name = self.file_path.stem.strip()
        
        from app.core.config import APP_DATA_DIR
        self.base_data_dir = APP_DATA_DIR
        if not self.base_data_dir.exists():
            self.base_data_dir.mkdir(parents=True, exist_ok=True)
            
    def _sanitize_path(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        # 替换非法字符为下划线
        return re.sub(r'[\\/*?:"<>|]', '_', filename)



    def process(self):
        """主要处理逻辑"""
        try:
            # 清理并创建书籍目录
            safe_book_name = self._sanitize_path(self.book_name)
            book_dir = self.base_data_dir / f"{safe_book_name}_audio"
            book_dir.mkdir(parents=True, exist_ok=True)
            
            tasks = []
            
            # 根据文件扩展名分发处理
            parser = ParserFactory.get_parser(str(self.file_path))
            tasks = parser.parse(self.file_path)

            if tasks:
                self._save_tasks(tasks, book_dir)
                logger.info(f"成功处理书籍 '{self.book_name}'，共生成 {len(tasks)} 个任务。")
            else:
                logger.warning(f"书籍 '{self.book_name}' 未提取到有效内容。")
                
        except Exception as e:
            logger.error(f"处理书籍 '{self.filename}' 时发生错误: {e}", exc_info=True)



    def _save_tasks(self, tasks: List[Dict[str, Any]], book_dir: pathlib.Path):
        """保存任务到数据库"""
        # 为了兼容性，暂时保留 tasks.json 生成 (可选)，但主要逻辑迁移到 DB
        # 这里演示直接存 DB
        
        from app.db.database import db
        safe_book_name = self._sanitize_path(self.book_name).strip()
        
        try:
            conn = db.conn
            if not conn:
                db.connect()
                conn = db.conn
                
            cursor = conn.cursor()
            
            # 检查是否已存在，如果存在则跳过或覆盖？
            # 简单起见，如果书籍已存在，应该先清理旧记录或只有增量更新
            # 这里假设重新导入是全量覆盖
            cursor.execute("DELETE FROM tasks WHERE book_name = ?", (safe_book_name,))
            
            # 批量插入
            data_to_insert = []
            for t in tasks:
                # task struct: {'id': 1, 'title': '...', 'content': '...', 'status': 'pending'}
                data_to_insert.append((
                    f"{safe_book_name}_{t['id']}", # task_id (unique string)
                    safe_book_name,
                    t['id'],
                    t['title'],
                    t['content'],
                    'pending',
                    None # audio_path
                ))
                
            cursor.executemany("""
                INSERT INTO tasks (id, book_name, chapter_index, title, content, status, audio_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            
            conn.commit()
            logger.info(f"成功将 {len(tasks)} 个任务保存到数据库。")
            
        except Exception as e:
            logger.error(f"保存任务到数据库失败: {e}", exc_info=True)

    def get_task_status(self) -> str:
        """获取当前书籍的处理进度"""
        safe_book_name = self._sanitize_path(self.book_name)
        task_file = self.base_data_dir / f"{safe_book_name}_audio" / "tasks.json"
        
        if not task_file.exists():
            return "任务文件不存在"
            
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                tasks = json.load(f)
            
            total = len(tasks)
            completed = sum(1 for t in tasks if t.get('status') == 'completed') # 假设 'completed' 状态
            
            return f"{completed}/{total}"
        except Exception as e:
            return f"读取进度失败: {e}"

# 简单的测试入口
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        processor = BookProcessor(sys.argv[1])
        processor.process()
        print(f"进度: {processor.get_task_status()}")
    else:
        print("请提供书籍文件路径作为参数")
