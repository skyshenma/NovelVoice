
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import pathlib
import asyncio

from app.api.api import api_router
# Ensure dirs created
from app.core.config import APP_DATA_DIR, CACHE_DIR

app = FastAPI(title="NovelVoice - AI Audiobook Generator")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router
app.include_router(api_router, prefix="/api")

# Static Files
# We assume static folder is in root, same level as app/
static_dir = pathlib.Path("static")
if not static_dir.exists():
    static_dir.mkdir()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index():
    return HTMLResponse(content=open("static/index.html", "r", encoding="utf-8").read())


# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 初始化日志系统
    from app.core.logger import setup_logger
    setup_logger()
    
    import logging
    logging.info("🚀 NovelVoice 启动完成")
    
    # 后台检查版本更新
    asyncio.create_task(check_version_on_startup())


async def check_version_on_startup():
    """启动时检查版本"""
    # 延迟 5 秒,避免影响启动速度
    await asyncio.sleep(5)
    
    from app.services.version_checker import version_checker
    await version_checker.check_update("edge-tts")
