import re
import pathlib
import chardet
from typing import List, Dict, Any
from .base import BaseParser

class TxtParser(BaseParser):
    def parse(self, file_path: pathlib.Path) -> List[Dict[str, Any]]:
        """
        Parse a TXT file into chapters using regex pattern matching and fallback to fixed-length splitting.
        """
        encoding = self._detect_encoding(file_path)
        print(f"Detected file encoding: {encoding}")
        
        chapter_pattern = re.compile(r'^\s*第.{1,7}[章节回].*')
        
        current_title = "开始"
        current_content = []
        tasks = []
        
        try:
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                for line in f:
                    stripped_line = line.strip()
                    if chapter_pattern.match(stripped_line):
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
                        current_title = stripped_line
                        current_content = []
                    else:
                        if stripped_line:
                            current_content.append(stripped_line)
                
                # Handling the last chapter
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
                        
            # Fallback: Fixed length splitting if no chapters found and content is long
            if len(tasks) <= 1 and (not tasks or len(tasks[0]['content']) > 5000):
                 # Refined fallback logic: if we have 1 task (Start) but it's huge, split it.
                 # Re-read content to be safe or use what we capture?
                 # We already have tasks[0] if valid.
                 
                 full_content = ""
                 if tasks:
                     full_content = tasks[0]['content']
                 else:
                     # Identify empty file case?
                     return []
                     
                 if len(full_content) > 5000:
                    print("No chapters detected, switching to fixed-length splitting (5000 chars/chunk)...")
                    tasks = []
                    chunk_size = 5000
                    total_length = len(full_content)
                    
                    for i in range(0, total_length, chunk_size):
                        chunk = full_content[i : i + chunk_size]
                        chunk_id = (i // chunk_size) + 1
                        tasks.append({
                            "id": chunk_id,
                            "title": f"第 {chunk_id} 部分",
                            "content": chunk,
                            "status": "pending",
                            "audio_path": ""
                        })
                        
            return tasks
            
        except Exception as e:
            print(f"Error parsing TXT file {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _detect_encoding(self, file_path: pathlib.Path) -> str:
        with open(file_path, 'rb') as f:
            rawdata = f.read(20000)
        result = chardet.detect(rawdata)
        encoding = result['encoding']
        return encoding if encoding else 'utf-8'

    def _clean_text(self, text: str) -> str:
        # Remove consecutive special characters
        text = re.sub(r'[\*_=]{3,}', '', text)
        # Remove separator lines
        text = re.sub(r'[-]{3,}', '', text)
        return text
