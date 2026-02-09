
import asyncio
import json
import os
import pathlib
import math
import aiofiles
import edge_tts
from typing import List, Dict, Any, Optional, Union, Callable
import logging

class DynamicSemaphore:
    """支持动态调整限制的信号量"""
    def __init__(self, limit_provider: Union[int, Callable[[], int]]):
        self.limit_provider = limit_provider if callable(limit_provider) else lambda: limit_provider
        self.current_count = 0
        self.condition = asyncio.Condition()

    async def __aenter__(self):
        async with self.condition:
            while self.current_count >= self.limit_provider():
                await self.condition.wait()
            self.current_count += 1

    async def __aexit__(self, exc_type, exc, tb):
        async with self.condition:
            self.current_count -= 1
            self.condition.notify_all()

class TTSProcessor:
    def __init__(self, book_dir: str, voice: str = "zh-CN-XiaoxiaoNeural", 
                 rate: str = "+0%", volume: str = "+0%", pitch: str = "+0Hz",
                 concurrency_limit: Union[int, Callable[[], int]] = 2,
                 notifier = None,
                 max_chars: Optional[int] = None,
                 timeout: Optional[int] = None,
                 max_logs: Optional[int] = None):
        self.book_dir = pathlib.Path(book_dir)

        # 移除 tasks.json 相关初始化
        # self.tasks_file = self.book_dir / "tasks.json" # DELETED
        
        # TTS 参数
        self.voice = voice
        # TTS 参数
        def clean_param(p, suffix):
            default = f"+0{suffix}"
            if p is None:
                return default
            
            s = str(p).strip()
            if not s:
                return default
                
            if s.isdigit() or (s.startswith(('+', '-')) and s[1:].isdigit()):
                return f"{s}{suffix}"
                
            if not s.endswith(suffix):
                s += suffix
            
            if s in [f"0{suffix}", f"-0{suffix}"]:
                 return default
                 
            return s

        self.rate = clean_param(rate, "%")
        self.volume = clean_param(volume, "%")
        self.pitch = clean_param(pitch, "Hz")
        
        # 长文本阈值（从配置读取）
        from app.core.config import MAX_CHARS
        self.max_chars = max_chars if max_chars is not None else MAX_CHARS
        
        # 超时时间（从配置读取）
        from app.core.config import TTS_TIMEOUT
        self.timeout = timeout if timeout is not None else TTS_TIMEOUT
        
        # 并发控制
        self.semaphore = DynamicSemaphore(concurrency_limit)
        # self.file_lock = asyncio.Lock() # 数据库有自己的锁机制，或者 SQLite 单写多读
        
        # 暂停控制 (默认运行)
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        
        # 状态追踪
        self.processing_chapters = set()
        
        # Bark 通知服务
        self.notifier = notifier
        
        # 日志系统
        from collections import deque
        import logging
        from app.core.config import MAX_LOGS
        log_limit = max_logs if max_logs is not None else MAX_LOGS
        self.logs = deque(maxlen=log_limit)
        
        self.logger = logging.getLogger("app.tts")
        
    def log(self, message: str, level: str = "INFO"):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        formatted = f"[{timestamp}] {message}"
        self.logs.append(formatted)
        
        log_msg = f"[{self.book_dir.name}] {message}"
        
        level = level.upper()
        if level == "ERROR":
            self.logger.error(log_msg)
        elif level == "WARNING":
            self.logger.warning(log_msg)
        elif level == "DEBUG":
            self.logger.debug(log_msg)
        else:
            self.logger.info(log_msg)
        
    def pause(self):
        self.log("任务暂停...")
        self.pause_event.clear()
        
    def resume(self):
        self.log("任务恢复...")
        self.pause_event.set()

    async def process(self, chapter_ids: Optional[List[str]] = None):
        """主处理流程"""
        
        # 确保开始时是运行状态
        if not self.pause_event.is_set():
            self.pause_event.set()

        # 读取任务 (从数据库)
        # 注意：这里我们使用同步的 database.py，为了不阻塞主循环，应该放到 thread pool 或者使用 aiosqlite
        # 既然前面 pip install aiosqlite 失败，我们先用 to_thread + sqlite3
        from app.db.database import db
        
        book_name = self.book_dir.name.replace("_audio", "")
        
        def fetch_tasks():
            cursor = db.get_cursor()
            query = "SELECT * FROM tasks WHERE book_name = ? ORDER BY chapter_index"
            cursor.execute(query, (book_name,))
            return [dict(row) for row in cursor.fetchall()]
            
        tasks = await asyncio.to_thread(fetch_tasks)
            
        # 筛选任务
        if chapter_ids:
            tasks = [t for t in tasks if str(t.get("chapter_index")) in map(str, chapter_ids)]
            self.log(f"筛选处理: {len(tasks)} 个章节")
            
        self.log(f"开始处理书籍: {book_name}, 共 {len(tasks)} 个章节")
        self.log(f"参数: Voice={self.voice}, Rate={self.rate}, Volume={self.volume}, Pitch={self.pitch}")

        # 📱 Bark 通知: 任务开始
        if self.notifier:
            await self.notifier.send_task_start(book_name, len(tasks))
        
        import time
        start_time = time.time()

        # 创建并执行所有任务
        # 限制：SQLite 默认不支持高并发写入，需要控制
        # 但我们使用 thread pool + 单连接或 WAL 模式应该还好
        coroutines = [self._process_task_wrapper(task) for task in tasks]
        await asyncio.gather(*coroutines)
        
        elapsed_minutes = (time.time() - start_time) / 60
        if self.notifier:
            await self.notifier.send_task_complete(book_name, elapsed_minutes)
        
        self.log(f"书籍 {book_name} 处理完成。")

    async def _process_task_wrapper(self, task: Dict[str, Any]):
        """任务包装器"""
        await self.pause_event.wait()
        
        title = task.get("title", "Unknown")
        self.processing_chapters.add(title)
        try:
            updated_task = await self._synthesize_chapter(task)
            if updated_task:
                await self._update_task_status_in_db(updated_task)
        finally:
            self.processing_chapters.discard(title)

    async def _update_task_status_in_db(self, task: Dict[str, Any]):
        from app.db.database import db
        
        def update_db():
            conn = db.conn
            if not conn:
                db.connect()
                conn = db.conn
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE tasks 
                SET status = ?, audio_path = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (task['status'], task.get('audio_path'), task['id']))
            conn.commit()
            
        await asyncio.to_thread(update_db)

    async def _synthesize_chapter(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """单个章节合成逻辑"""
        # 适配 DB 字段名
        task_id = task.get("id") # DB id is string "bookname_idx"
        chapter_index = task.get("chapter_index")
        title = task.get("title")
        content = task.get("content")
        status = task.get("status")
        audio_path_db = task.get("audio_path")
        
        safe_title = str(title).replace("/", "_").replace("\\", "_")
        filename = f"{chapter_index:04d}-{safe_title}.mp3"
        output_path = self.book_dir / filename
        
        # 1. 检查断点续传
        # 数据库显示完成，或者文件存在且不为空
        if status == "completed" and output_path.exists() and output_path.stat().st_size > 0:
            return None 
            
        # 如果文件存在但数据库说是 pending，可能是之前没更新成功，这里也检查一下文件
        # 或者我们强制覆盖
        
        async with self.semaphore:
            self.log(f"[{chapter_index}] 开始合成: {title} (长度: {len(content)})")
            
            try:
                if len(content) > self.max_chars:
                    self.log(f"[{chapter_index}] 文本过长，执行切割处理...")
                    await self._synthesize_long_text(content, output_path)
                else:
                    await self._synthesize_with_retry(content, output_path)
                
                # 3. 更新状态
                newTask = dict(task) # shallow copy
                newTask["status"] = "completed"
                newTask["audio_path"] = str(output_path.name)
                self.log(f"[{chapter_index}] 合成完成: {filename}")
                return newTask
                
            except Exception as e:
                self.log(f"[{chapter_index}] 合成失败: {e}")
                newTask = dict(task)
                newTask["status"] = "failed"
                return newTask

    async def _synthesize_with_retry(self, text: str, output_path: pathlib.Path, max_retries: int = 3):
        """带重试的合成 (Timeout + Exponential Backoff)"""
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(
                    text, 
                    self.voice, 
                    rate=self.rate, 
                    volume=self.volume, 
                    pitch=self.pitch
                )
                await asyncio.wait_for(communicate.save(str(output_path)), timeout=self.timeout)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    return
                else:
                    raise Exception("生成的文件为空")
                    
            except Exception as e:
                wait_time = 2 * (2 ** attempt) 
                wait_time = min(wait_time, 30)
                
                if attempt < max_retries - 1:
                    self.log(f"合成重试 ({attempt+1}/{max_retries}) 失败: {e}, 等待 {wait_time}s...", level="WARNING")
                    await asyncio.sleep(wait_time)
                else:
                    self.log(f"最终失败: {e}", level="ERROR")
                    raise e

    async def _synthesize_long_text(self, text: str, output_path: pathlib.Path):
        """长文本切割合成并合并"""
        from app.core.text_splitter import TextSplitter
        splitter = TextSplitter()
        chunks = splitter.split_text(text, self.max_chars)
        
        self.log(f"智能切分: {len(text)} 字符 -> {len(chunks)} 片段")

        # 分别合成
        temp_files = []
        try:
            for i, chunk in enumerate(chunks):
                temp_file = output_path.with_name(f"{output_path.stem}_part{i}.mp3")
                temp_files.append(temp_file)
                await self._synthesize_with_retry(chunk, temp_file)
            
            async with aiofiles.open(output_path, 'wb') as outfile:
                for temp_file in temp_files:
                    async with aiofiles.open(temp_file, 'rb') as infile:
                        data = await infile.read()
                        await outfile.write(data)
                        
        finally:
            for f in temp_files:
                if f.exists():
                    f.unlink()

    async def preview_speech(self, text: str, max_chars: int = 50) -> bytes:
        """生成预览音频 (仅内存)"""
        import io
        preview_text = text[:max_chars]
        
        communicate = edge_tts.Communicate(
            preview_text, 
            self.voice, 
            rate=self.rate, 
            volume=self.volume, 
            pitch=self.pitch
        )
        
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
                
        buffer.seek(0)
        return buffer.read()

# CLI 入口
if __name__ == "__main__":
    import sys
    import argparse
    # 注意：CLI 模式现在也需要连接数据库，这可能需要在 __main__ 里初始化 DB
    # 暂时简化，提示用户使用 Web 界面
    print("CLI 模式暂时不支持直接运行，请使用 Web 界面或通过 curl 调用 API")
