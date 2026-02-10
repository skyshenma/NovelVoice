import asyncio
from typing import List
from fastapi import WebSocket
import logging

class LogConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.log_queue = asyncio.Queue()
        self._broadcasting = False

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

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
                message = await self.log_queue.get()
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

    def put_log(self, message: str):
        """Called by logic (sync or async) to put log into broadcast queue"""
        # Try to use stored loop for thread-safe access
        try:
            if hasattr(self, 'loop') and self.loop:
                self.loop.call_soon_threadsafe(self.log_queue.put_nowait, message)
            else:
                # Fallback to current loop if possible
                loop = asyncio.get_running_loop()
                loop.call_soon_threadsafe(self.log_queue.put_nowait, message)
        except Exception as e:
            # Fallback for sync threads without loop access at startup/shutdown
            print(f"⚠️ Log queue failed for: {message[:50]}... Error: {e}")

log_manager = LogConnectionManager()
