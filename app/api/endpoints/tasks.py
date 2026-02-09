
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import List, Optional

from app.core.config import APP_DATA_DIR, BARK_ENABLED, BARK_SERVER_URL, BARK_API_KEY, WEB_BASE_URL, config
from app.core.state import state
from app.services.tts_engine import TTSProcessor
from app.services.notifier import BarkNotifier
from app.schemas.config import GenerateRequest, TTSConfig

router = APIRouter()

import logging

# 获取 logger
logger = logging.getLogger(__name__)

async def run_tts_task(book_name: str, tts_config: TTSConfig, chapter_ids: Optional[List[int]] = None):
    try:
        book_dir = APP_DATA_DIR / f"{book_name}_audio"
        if not book_dir.exists():
            logger.error(f"Directory not found for {book_name}")
            return

        # Initialize Bark Notifier with configuration
        # 使用全局 config 对象获取配置
        silent_hours_config = config.get_section("bark.silent_hours")
        http_timeout = config.get("bark.http_timeout", 5)
        
        notifier = BarkNotifier(
            server_url=BARK_SERVER_URL,
            api_key=BARK_API_KEY,
            enabled=BARK_ENABLED,
            web_base_url=WEB_BASE_URL,
            silent_hours_config=silent_hours_config,
            http_timeout=http_timeout
        )

        # Initialize Processor
        processor = TTSProcessor(
            str(book_dir),
            voice=tts_config.voice,
            rate=tts_config.rate,
            volume=tts_config.volume,
            pitch=tts_config.pitch,
            concurrency_limit=lambda: state.concurrency,
            notifier=notifier
        )
        
        # Update global state
        state.active_processors[book_name] = processor 
        
        # Convert chapter_ids to string list if processor expects that?
        # Processor.process expects Optional[List[str]] based on type hint in tts_processor.py?
        # Let's check tts_processor.py line 105: process(self, chapter_ids: Optional[List[str]] = None)
        # But GenerateRequest.chapter_ids is List[int].
        # We should convert.
        ids_str = [str(i) for i in chapter_ids] if chapter_ids else None
        
        logger.info(f"Starting TTS task for {book_name} with voice {tts_config.voice}")
        await processor.process(chapter_ids=ids_str)
            
    except Exception as e:
        logger.error(f"Error processing {book_name}: {e}", exc_info=True)
    finally:
        if book_name in state.active_processors:
            del state.active_processors[book_name]

@router.post("/start")
async def start_task(request: GenerateRequest, background_tasks: BackgroundTasks):
    if request.book_name in state.active_processors:
        # If running, check if just paused
        processor = state.active_processors[request.book_name]
        if not processor.pause_event.is_set():
             processor.resume()
             return {"message": f"Resumed task for {request.book_name}"}
        return {"message": f"Task for {request.book_name} is already running."}
    
    background_tasks.add_task(run_tts_task, request.book_name, request.config, request.chapter_ids)
    return {"message": f"Started generating audio for {request.book_name}"}

@router.post("/pause/{book_name}")
async def pause_task(book_name: str):
    if book_name in state.active_processors:
        state.active_processors[book_name].pause()
        return {"message": f"Paused task for {book_name}"}
    return {"message": "Task not running", "status": "error"}

@router.post("/resume/{book_name}")
async def resume_task(book_name: str):
    if book_name in state.active_processors:
        state.active_processors[book_name].resume()
        return {"message": f"Resumed task for {book_name}"}
    return {"message": "Task not running", "status": "error"}

@router.get("/status/{book_name}")
async def task_status(book_name: str):
    if book_name in state.active_processors:
        processor = state.active_processors[book_name]
        return {
            "is_running": True,
            "is_paused": not processor.pause_event.is_set(),
            "current_chapter": list(processor.processing_chapters)
        }
    return {"is_running": False, "is_paused": False, "current_chapter": []}

@router.get("/logs/{book_name}")
async def get_logs(book_name: str):
    if book_name in state.active_processors:
        return {"logs": list(state.active_processors[book_name].logs)}
    return {"logs": []}

@router.post("/concurrency")
async def set_concurrency(limit: int = Query(..., ge=1, le=10)):
    state.concurrency = limit
    return {"message": f"Concurrency set to {limit}", "effective_next_chapter": True}
        
