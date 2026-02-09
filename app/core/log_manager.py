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
        while True:
            try:
                message = await self.log_queue.get()
                await self._broadcast(message)
            except Exception as e:
                print(f"Error broadcasting log: {e}")
                
    async def _broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # If sending fails, remove the connection
                self.disconnect(connection)

    def put_log(self, message: str):
        """Called by logging handler (sync) to put log into async queue"""
        # We need to access the loop safely
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(self.log_queue.put_nowait, message)
        except RuntimeError:
            # No running loop (e.g. during startup/shutdown), ignore or print
            pass

log_manager = LogConnectionManager()
