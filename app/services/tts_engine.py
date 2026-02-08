
import asyncio
import json
import os
import pathlib
import math
import aiofiles
import edge_tts
from typing import List, Dict, Any, Optional, Union, Callable

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
                 notifier = None):
        self.book_dir = pathlib.Path(book_dir)
        self.tasks_file = self.book_dir / "tasks.json"
        
        # TTS 参数
        self.voice = voice
        # TTS 参数
        # Treat "0" values as None to use default
        def clean_param(p, suffix):
            if not p: return None
            s = p.strip()
            if s in ["0", "+0", "-0", "0"+suffix, "+0"+suffix, "-0"+suffix]:
                return None
            return s

        self.rate = clean_param(rate, "%")
        self.volume = clean_param(volume, "%")
        self.pitch = clean_param(pitch, "Hz")
        
        # 长文本阈值
        self.max_chars = 8000
        
        # 并发控制
        self.semaphore = DynamicSemaphore(concurrency_limit)
        self.file_lock = asyncio.Lock()
        
        # 暂停控制 (默认运行)
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        
        # 状态追踪
        self.processing_chapters = set()
        
        # Bark 通知服务
        self.notifier = notifier
        
        # 日志系统
        from collections import deque
        from datetime import datetime
        import logging
        self.logs = deque(maxlen=200) # Keep last 200 logs
        
        # Configure file logger
        self.logger = logging.getLogger(f"TTS_{self.book_dir.name}")
        self.logger.setLevel(logging.ERROR)
        
        # Only add handler if it doesn't exist
        # Check by type to avoid adding multiple FileHandlers
        has_file_handler = any(isinstance(h, logging.FileHandler) for h in self.logger.handlers)
        if not has_file_handler:
            try:
                handler = logging.FileHandler(self.book_dir / "error.log", encoding='utf-8')
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
            except Exception as e:
                print(f"Failed to setup file logger: {e}")
        
    def log(self, message: str, level: str = "INFO"):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        print(formatted)
        self.logs.append(formatted)
        
        if level == "ERROR":
            self.logger.error(message)
        
    def pause(self):
        self.log("任务暂停...")
        self.pause_event.clear()
        
    def resume(self):
        self.log("任务恢复...")
        self.pause_event.set()

    async def process(self, chapter_ids: Optional[List[str]] = None):
        """主处理流程"""
        # 信号量已在 init 中初始化
        # self.semaphore = asyncio.Semaphore(2)
        
        if not self.tasks_file.exists():
            self.log(f"任务文件不存在: {self.tasks_file}")
            return
            
        # 确保开始时是运行状态
        if not self.pause_event.is_set():
            self.pause_event.set()

        # 读取任务
        async with aiofiles.open(self.tasks_file, 'r', encoding='utf-8') as f:
            content = await f.read()
            tasks = json.loads(content)
            
        # 筛选任务
        if chapter_ids:
            tasks = [t for t in tasks if str(t.get("id")) in map(str, chapter_ids)]
            self.log(f"筛选处理: {len(tasks)} 个章节")
            
        self.log(f"开始处理书籍: {self.book_dir.name}, 共 {len(tasks)} 个章节")
        self.log(f"参数: Voice={self.voice}, Rate={self.rate}, Volume={self.volume}, Pitch={self.pitch}")

        # 📱 Bark 通知: 任务开始
        book_name = self.book_dir.name.replace("_audio", "")
        if self.notifier:
            await self.notifier.send_task_start(book_name, len(tasks))
        
        # 记录开始时间（用于耗时统计）
        import time
        start_time = time.time()

        # 创建并执行所有任务
        coroutines = [self._process_task_wrapper(task) for task in tasks]
        await asyncio.gather(*coroutines)
        
        # 📱 Bark 通知: 任务完成
        elapsed_minutes = (time.time() - start_time) / 60
        if self.notifier:
            await self.notifier.send_task_complete(book_name, elapsed_minutes)
        
        self.log(f"书籍 {self.book_dir.name} 处理完成。")

    async def _process_task_wrapper(self, task: Dict[str, Any]):
        """任务包装器，用于在完成后更新整体状态文件（可选，或仅在内存中更新）"""
        
        # 每一章开始前检查暂停状态
        await self.pause_event.wait()
        
        # 记录正在处理
        self.processing_chapters.add(task.get("title", "Unknown"))
        try:
            # 注意：这里为了简化，每个任务完成后单独更新文件可能会有竞争。
            # 更好的做法是内存更新，最后统一保存，或者使用锁。
            # 但考虑到断点续传，实时更新状态到文件更安全。
            # 这里采用简单的实时更新，实际高并发可能需要文件锁，但 2 个并发冲突概率极低。
            
            updated_task = await self._synthesize_chapter(task)
            if updated_task:
                await self._update_task_status_in_file(updated_task)
        finally:
            self.processing_chapters.discard(task.get("title", "Unknown"))

    async def _update_task_status_in_file(self, task: Dict[str, Any]):
        async with self.file_lock:
             try:
                 async with aiofiles.open(self.tasks_file, 'r', encoding='utf-8') as f:
                     content = await f.read()
                     tasks = json.loads(content)
                 
                 for i, t in enumerate(tasks):
                     if t['id'] == task['id']:
                         tasks[i] = task
                         break
                         
                 async with aiofiles.open(self.tasks_file, 'w', encoding='utf-8') as f:
                     await f.write(json.dumps(tasks, ensure_ascii=False, indent=2))
             except Exception as e:
                 self.log(f"更新状态文件失败: {e}")

    async def _synthesize_chapter(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """单个章节合成逻辑"""
        task_id = task.get("id")
        title = task.get("title")
        content = task.get("content")
        status = task.get("status")
        
        # 文件名格式: 0001-第一章.mp3
        safe_title = str(title).replace("/", "_").replace("\\", "_")
        filename = f"{task_id:04d}-{safe_title}.mp3"
        output_path = self.book_dir / filename
        
        # 1. 检查断点续传
        if status == "completed" and output_path.exists() and output_path.stat().st_size > 0:
            # self.log(f"[{task_id}] 跳过已完成任务: {title}")
            return None # 不需要更新

        async with self.semaphore:
            self.log(f"[{task_id}] 开始合成: {title} (长度: {len(content)})")
            
            try:
                # 2. 长文本切割
                if len(content) > self.max_chars:
                    self.log(f"[{task_id}] 文本过长，执行切割处理...")
                    await self._synthesize_long_text(content, output_path)
                else:
                    await self._synthesize_with_retry(content, output_path)
                
                # 3. 更新状态
                task["status"] = "completed"
                task["audio_path"] = str(output_path.name)
                self.log(f"[{task_id}] 合成完成: {filename}")
                return task
                
            except Exception as e:
                self.log(f"[{task_id}] 合成失败: {e}")
                task["status"] = "failed"
                return task

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
                # 增加超时控制 (30s)
                await asyncio.wait_for(communicate.save(str(output_path)), timeout=30.0)
                
                # 验证文件
                if output_path.exists() and output_path.stat().st_size > 0:
                    return
                else:
                    raise Exception("生成的文件为空")
                    
            except Exception as e:
                # 指数退避: 2s, 4s, 8s...
                wait_time = 2 * (2 ** attempt) 
                # 限制最大等待时间
                wait_time = min(wait_time, 30)
                
                if attempt < max_retries - 1:
                    self.log(f"合成重试 ({attempt+1}/{max_retries}) 失败: {e}, 等待 {wait_time}s...", level="WARNING")
                    await asyncio.sleep(wait_time)
                else:
                    self.log(f"最终失败: {e}", level="ERROR")
                    # 📱 Bark 通知: 异常报警（仅在最终失败时推送）
                    # Note: We don't have task_id and book_name here easily
                    # This would need to be passed down or extracted from context
                    raise e

    async def _synthesize_long_text(self, text: str, output_path: pathlib.Path):
        """长文本切割合成并合并"""
        # 切分文本
        chunks = []
        current_chunk = ""
        # 简单按长度切分，更好的是按句号切分，这里简化处理防止截断句子
        # 稍微优化：寻找最近的标点符号
        
        idx = 0
        while idx < len(text):
            end_idx = min(idx + self.max_chars, len(text))
            
            if end_idx < len(text):
                # 尝试在最后 100 个字符找标点
                lookback = text[end_idx-100:end_idx]
                last_punct = max(lookback.rfind('。'), lookback.rfind('\n'), lookback.rfind('！'), lookback.rfind('？'))
                if last_punct != -1:
                    end_idx = (end_idx - 100) + last_punct + 1
            
            chunks.append(text[idx:end_idx])
            idx = end_idx

        # 分别合成
        temp_files = []
        try:
            for i, chunk in enumerate(chunks):
                temp_file = output_path.with_name(f"{output_path.stem}_part{i}.mp3")
                temp_files.append(temp_file)
                await self._synthesize_with_retry(chunk, temp_file)
            
            # 合并文件 (MP3 直接追加即可)
            async with aiofiles.open(output_path, 'wb') as outfile:
                for temp_file in temp_files:
                    async with aiofiles.open(temp_file, 'rb') as infile:
                        data = await infile.read()
                        await outfile.write(data)
                        
        finally:
            # 清理临时文件
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

    async def _update_task_status_in_file(self, updated_task: Dict[str, Any]):
        """更新文件中的特定任务状态"""
        # 使用 asyncio.Lock 保护文件写入，防止并发导致的 JSON 损坏
        async with self.file_lock:
            try:
                if not self.tasks_file.exists():
                    return

                async with aiofiles.open(self.tasks_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    current_tasks = json.loads(content)
                
                updated = False
                for t in current_tasks:
                    if t['id'] == updated_task['id']:
                        t.update(updated_task)
                        updated = True
                        break
                
                if updated:
                    async with aiofiles.open(self.tasks_file, 'w', encoding='utf-8') as f:
                        await f.write(json.dumps(current_tasks, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"更新任务状态失败: {e}")

# CLI 入口
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="TTS Processor")
    parser.add_argument("book_dir", help="书籍音频目录路径")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="发音人")
    parser.add_argument("--rate", default="+0%", help="语速")
    parser.add_argument("--volume", default="+0%", help="音量")
    parser.add_argument("--pitch", default="+0Hz", help="音调")
    
    args = parser.parse_args()
    
    processor = TTSProcessor(args.book_dir, args.voice, args.rate, args.volume, args.pitch)
    asyncio.run(processor.process())
