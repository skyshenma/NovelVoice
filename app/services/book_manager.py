import os
import re
import json
import shutil
import pathlib
import chardet
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from typing import List, Dict, Any

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

    def _clean_text(self, text: str) -> str:
        """清洗文本中的干扰符号"""
        # 1. 移除连续的特殊符号 (如 ***, ___, ===)
        text = re.sub(r'[\*_=]{3,}', '', text)
        # 2. 移除常见的分割线 (如 ---------)
        text = re.sub(r'[-]{3,}', '', text)
        return text

    def process(self):
        """主要处理逻辑"""
        try:
            # 清理并创建书籍目录
            safe_book_name = self._sanitize_path(self.book_name)
            book_dir = self.base_data_dir / f"{safe_book_name}_audio"
            book_dir.mkdir(parents=True, exist_ok=True)
            
            tasks = []
            
            # 根据文件扩展名分发处理
            suffix = self.file_path.suffix.lower()
            if suffix == '.txt':
                tasks = self._process_txt()
            elif suffix == '.epub':
                tasks = self._process_epub()
            else:
                print(f"不支持的文件格式: {suffix}")
                return

            if tasks:
                self._save_tasks(tasks, book_dir)
                print(f"成功处理书籍 '{self.book_name}'，共生成 {len(tasks)} 个任务。")
            else:
                print(f"书籍 '{self.book_name}' 未提取到有效内容。")
                
        except Exception as e:
            print(f"处理书籍 '{self.filename}' 时发生错误: {e}")
            import traceback
            traceback.print_exc()

    def _detect_encoding(self, file_path: pathlib.Path) -> str:
        """读取文件前 20KB 检测编码"""
        with open(file_path, 'rb') as f:
            rawdata = f.read(20000)
        result = chardet.detect(rawdata)
        encoding = result['encoding']
        return encoding if encoding else 'utf-8'

    def _process_txt(self) -> List[Dict[str, Any]]:
        """处理 TXT 文件，支持正则分章和定长分章"""
        tasks = []
        encoding = self._detect_encoding(self.file_path)
        print(f"检测到文件编码: {encoding}")
        
        chapter_pattern = re.compile(r'^\s*第.{1,7}[章节回].*')
        
        current_title = "开始"
        current_content = []
        tasks = []
        
        # 内存优化：流式读取
        with open(self.file_path, 'r', encoding=encoding, errors='replace') as f:
            for line in f:
                stripped_line = line.strip()
                if chapter_pattern.match(stripped_line):
                    # 发现新章节，保存上一章节（如果有内容）
                    if current_content:
                        content_str = "\n".join(current_content).strip()
                        if content_str:
                            tasks.append({
                                "id": len(tasks) + 1,
                                "title": current_title,
                                "content": self._clean_text(content_str),
                                "status": "pending",
                                "audio_path": ""
                            })
                    # 重置状态
                    current_title = stripped_line
                    current_content = []
                else:
                    if stripped_line: # 只要非空行都保留，或者根据需求过滤
                        current_content.append(stripped_line)
            
            # 保存最后一个章节
            if current_content:
                content_str = "\n".join(current_content).strip()
                if content_str:
                    tasks.append({
                        "id": len(tasks) + 1,
                        "title": current_title,
                        "content": content_str,
                        "status": "pending",
                        "audio_path": ""
                    })

        # 后处理：如果只生成了一个任务（说明没匹配到正则），且内容很长，则按长度切分
        if len(tasks) == 1 and len(tasks[0]['content']) > 5000:
            original_content = tasks[0]['content']
            print("未检测到明显章节结构，切换为定长切分模式 (5000字/章)...")
            
            # 清空原任务列表，重新切分
            tasks = []
            chunk_size = 5000
            total_length = len(original_content)
            
            for i in range(0, total_length, chunk_size):
                chunk = original_content[i : i + chunk_size]
                chunk_id = (i // chunk_size) + 1
                tasks.append({
                    "id": chunk_id,
                    "title": f"第 {chunk_id} 部分",
                    "content": chunk,
                    "status": "pending",
                    "audio_path": ""
                })

        return tasks

    def _process_epub(self) -> List[Dict[str, Any]]:
        """处理 EPUB 文件"""
        tasks = []
        try:
            book = epub.read_epub(str(self.file_path))
            
            # 遍历文档项
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    # 使用 BS4 提取文本
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    # 尝试获取标题
                    title = ""
                    if soup.title and soup.title.string:
                        title = soup.title.string.strip()
                    else:
                        # 尝试找 h1-h2
                        h_tag = soup.find(['h1', 'h2'])
                        if h_tag:
                            title = h_tag.get_text().strip()
                        else:
                            # 默认文件名或ID
                            title = item.get_name()

                    # 获取正文文本
                    text_content = soup.get_text(separator='\n').strip()
                    
                    # 过滤短内容（如目录页、版权页、空页）
                    if len(text_content) < 50:
                        continue
                        
                    tasks.append({
                        "id": len(tasks) + 1,
                        "title": title,
                        "content": text_content,
                        "status": "pending",
                        "audio_path": ""
                    })
        except Exception as e:
            print(f"EPUB 解析失败: {e}")
            
        return tasks

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
