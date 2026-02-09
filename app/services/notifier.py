
import aiohttp
import asyncio
from typing import Optional
from datetime import datetime, time
import os
import logging

logger = logging.getLogger(__name__)

class BarkNotifier:
    """Bark 推送通知服务"""
    
    def __init__(
        self, 
        server_url: str = "", 
        api_key: str = "", 
        enabled: bool = False,
        web_base_url: str = "http://localhost:8000",
        silent_hours_config: Optional[dict] = None,
        http_timeout: Optional[int] = None
    ):
        self.server_url = server_url.rstrip('/') if server_url else ""
        self.api_key = api_key
        self.enabled = enabled and server_url and api_key
        self.web_base_url = web_base_url
        
        # 静默时间段配置（从配置读取）
        if silent_hours_config and silent_hours_config.get('enabled', True):
            start_str = silent_hours_config.get('start', '22:00')
            end_str = silent_hours_config.get('end', '08:00')
            start_hour, start_min = map(int, start_str.split(':'))
            end_hour, end_min = map(int, end_str.split(':'))
            self.silent_start = time(start_hour, start_min)
            self.silent_end = time(end_hour, end_min)
            self.silent_enabled = True
        else:
            # 默认值：22:00 - 08:00
            self.silent_start = time(22, 0)
            self.silent_end = time(8, 0)
            self.silent_enabled = False
        
        # HTTP 超时时间（从配置读取）
        self.http_timeout = http_timeout if http_timeout is not None else 5
        
    def is_silent_period(self) -> bool:
        """检查是否在静默时间段"""
        if not self.silent_enabled:
            return False
        
        now = datetime.now().time()
        if self.silent_start > self.silent_end:
            # 跨越午夜的情况 (22:00 - 08:00)
            return now >= self.silent_start or now <= self.silent_end
        return self.silent_start <= now <= self.silent_end
    
    async def send(
        self, 
        title: str, 
        content: str, 
        group: Optional[str] = None,
        url: Optional[str] = None
    ) -> bool:
        """
        发送 Bark 通知
        
        Args:
            title: 通知标题
            content: 通知内容
            group: 分组名称（用于折叠通知）
            url: 点击跳转的 URL
            
        Returns:
            bool: 是否发送成功
        """
        if not self.enabled:
            return False
            
        if self.is_silent_period():
            logger.info(f"[Bark] 静默时间段，跳过推送: {title}")
            return False
        
        try:
            # 构建 Bark URL
            # 格式: https://api.day.app/{key}/{title}/{content}?group=xxx&url=xxx
            bark_url = f"{self.server_url}/{self.api_key}/{title}/{content}"
            params = {}
            
            if group:
                params['group'] = group
            if url:
                params['url'] = url
            
            # 发送异步请求（使用配置的超时时间）
            timeout = aiohttp.ClientTimeout(total=self.http_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(bark_url, params=params) as resp:
                    if resp.status == 200:
                        logger.info(f"[Bark] ✅ 推送成功: {title}")
                        return True
                    else:
                        logger.warning(f"[Bark] ❌ 推送失败 (HTTP {resp.status}): {title}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.warning(f"[Bark] ⏱️ 推送超时（不影响主流程）: {title}")
            return False
        except Exception as e:
            logger.error(f"[Bark] ⚠️ 推送异常（不影响主流程）: {e}")
            return False
    
    async def send_task_start(self, book_name: str, total_chapters: int) -> bool:
        """任务开始通知"""
        return await self.send(
            title="📚 任务开始",
            content=f"《{book_name}》已加入队列，共 {total_chapters} 章",
            group=book_name,
            url=f"{self.web_base_url}/#book={book_name}"
        )
    
    async def send_task_complete(self, book_name: str, elapsed_minutes: float) -> bool:
        """任务完成通知"""
        return await self.send(
            title="✅ 生成完成",
            content=f"《{book_name}》已完成！耗时 {elapsed_minutes:.0f} 分钟",
            group=book_name,
            url=f"{self.web_base_url}/#book={book_name}"
        )
    
    async def send_task_error(self, book_name: str, chapter_id: int, error_msg: str = "") -> bool:
        """任务错误通知"""
        msg = f"《{book_name}》章节 {chapter_id} 重试失败"
        if error_msg:
            msg += f": {error_msg}"
        return await self.send(
            title="⚠️ 生成失败",
            content=msg,
            group=book_name,
            url=f"{self.web_base_url}/#book={book_name}"
        )
    
    async def send_task_progress(self, book_name: str, completed: int, total: int) -> bool:
        """任务进度通知（可选）"""
        progress = int(completed / total * 100)
        return await self.send(
            title="📊 进度更新",
            content=f"《{book_name}》已完成 {progress}% ({completed}/{total})",
            group=book_name,
            url=f"{self.web_base_url}/#book={book_name}"
        )
    
    async def send_test(self) -> bool:
        """发送测试通知"""
        return await self.send(
            title="🔔 测试通知",
            content="Bark 配置正确，推送服务正常！",
            url=self.web_base_url
        )
