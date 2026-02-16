import asyncio
from typing import List, Dict, Any, Optional
from fastapi import WebSocket
import logging
import json
import time
import os
from collections import deque
from pathlib import Path
from app.core.config import APP_DATA_DIR

# Ensure logs directory exists
LOG_DIR = APP_DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
OPERATION_LOG_FILE = LOG_DIR / "operation.log"

class LogConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.log_queue = asyncio.Queue()
        self._broadcasting = False
        # Store last 200 logs in memory
        self.history: deque = deque(maxlen=200)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send history upon connection
        if self.history:
            history_list = list(self.history)
            for log_entry in history_list:
                await self._send_to_connection(websocket, json.dumps(log_entry, ensure_ascii=False))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def start_broadcasting(self):
        """Starts the background task to consume logs from queue and broadcast"""
        if self._broadcasting:
            return
        self._broadcasting = True
        self.loop = asyncio.get_running_loop() # Store the loop for cross-thread access
        
        # Start heartbeat task
        asyncio.create_task(self._heartbeat())
        
        while True:
            try:
                log_entry = await self.log_queue.get()
                
                # Persist critical logs
                self._persist_log(log_entry)
                
                # Broadcast to WS clients
                message = json.dumps(log_entry, ensure_ascii=False)
                await self._broadcast(message)
            except Exception as e:
                print(f"Error broadcasting log: {e}")

    async def _heartbeat(self):
        """Sends a ping every 30s to keep connections alive"""
        while True:
            await asyncio.sleep(30)
            if self.active_connections:
                await self._broadcast("_PING_")
                
    async def _broadcast(self, message: str):
        # Create tasks for all connections to avoid blocking if one hangs
        tasks = []
        for connection in self.active_connections[:]: # Copy list to avoid modification during iteration
            tasks.append(self._send_to_connection(connection, message))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_connection(self, connection: WebSocket, message: str):
        try:
            await connection.send_text(message)
        except Exception:
            self.disconnect(connection)

    def _persist_log(self, log_entry: Dict[str, Any]):
        """Write critical operations to disk"""
        try:
            msg = log_entry.get("message", "")
            level = log_entry.get("level", "info")
            
            # Criteria for persistence: 
            # 1. Level is error/success
            # 2. Keywords like "delete", "stop", "cancel", "failed"
            keywords = ["删除", "中止", "失败", "failed", "delete", "cancel", "打包完成"]
            should_persist = level in ["error", "success"] or any(k in msg for k in keywords)

            if should_persist:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(log_entry["timestamp"]))
                line = f"[{timestamp}] [{level.upper()}] {msg}\n"
                with open(OPERATION_LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(line)
        except Exception as e:
            print(f"Failed to persist log: {e}")

    def put_log(self, message: str, level: str = "info", category: str = "system"):
        """Called by logic (sync or async) to put log into broadcast queue"""
        
        log_entry = {
            "message": message,
            "level": level,
            "category": category,
            "timestamp": time.time()
        }
        
        # Add to history immediately (thread-safe deque)
        self.history.append(log_entry)

        # Try to use stored loop for thread-safe access
        try:
            if hasattr(self, 'loop') and self.loop:
                self.loop.call_soon_threadsafe(self.log_queue.put_nowait, log_entry)
            else:
                # Fallback to current loop if possible
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self.log_queue.put_nowait, log_entry)
        except Exception as e:
            # Fallback for sync threads without loop access at startup/shutdown
            print(f"⚠️ Log queue failed for: {message[:50]}... Error: {e}")

log_manager = LogConnectionManager()
