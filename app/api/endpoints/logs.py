from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.log_manager import log_manager
import asyncio

router = APIRouter()

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await log_manager.connect(websocket)
    try:
        # 保持连接活跃，也可以接收前端发来的指令（例如调整日志级别，暂未实现）
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        log_manager.disconnect(websocket)
