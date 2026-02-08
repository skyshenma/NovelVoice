import os
import re
import json
import shutil
import pathlib
import shutil
import pathlib
from typing import List, Dict, Any
from .parsers import ParserFactory

class BookProcessor:
    def __init__(self, file_path: str):
        self.file_path = pathlib.Path(file_path)
        self.filename = self.file_path.name
        self.book_name = self.file_path.stem
        
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
                print(f"成功处理书籍 '{self.book_name}'，共生成 {len(tasks)} 个任务。")
            else:
                print(f"书籍 '{self.book_name}' 未提取到有效内容。")
                
        except Exception as e:
            print(f"处理书籍 '{self.filename}' 时发生错误: {e}")
            import traceback
            traceback.print_exc()



    def _save_tasks(self, tasks: List[Dict[str, Any]], book_dir: pathlib.Path):
        """保存任务到 JSON"""
        task_file = book_dir / "tasks.json"
        try:
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
            print(f"任务列表已保存至: {task_file}")
        except Exception as e:
            print(f"任务文件保存失败: {e}")

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
