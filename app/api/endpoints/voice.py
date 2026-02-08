
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
import hashlib
import io
import edge_tts

from app.core.config import VOICES_LIST, APP_DATA_DIR, CACHE_DIR, WEB_BASE_URL, config
from app.schemas.config import CustomPreviewRequest, TTSConfig, PreviewRequest
from app.services.tts_engine import TTSProcessor

router = APIRouter()

@router.get("/voices") # /api/voices
async def get_voices():
    return VOICES_LIST

@router.get("/voice/preview/{short_name}")
async def preview_voice_cached(
    short_name: str,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz"
):
    """Get cached voice preview."""
    
    # Directory is CACHE_DIR (which we mapped to data/app/previews or data/cache)
    # Let's use CACHE_DIR from config
    
    # 2. Hash parameters
    param_str = f"{short_name}_{rate}_{volume}_{pitch}"
    param_hash = hashlib.md5(param_str.encode()).hexdigest()
    filename = f"{short_name}_{param_hash}.mp3"
    file_path = CACHE_DIR / filename

    # 3. Check Cache
    if file_path.exists():
        return FileResponse(file_path, media_type="audio/mpeg")

    # 4. Generate if not exists
    gender = "Female" # Default
    for v in VOICES_LIST:
        if v["ShortName"] == short_name:
            gender = v.get("Gender", "Female")
            break
    
    if gender == "Male":
        text = "这里是 Edge TTS 语音合成测试，希望能为您带来优质的听觉体验。"
    else:
        text = "您好，我是微软智能语音助手，这段音频是为了测试我的发音效果。"

    try:
        communicate = edge_tts.Communicate(
            text, 
            short_name, 
            rate=rate, 
            volume=volume, 
            pitch=pitch
        )
        await communicate.save(str(file_path))
        
        return FileResponse(file_path, media_type="audio/mpeg")
    except Exception as e:
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")

@router.post("/voice/preview_custom")
async def preview_custom(request: CustomPreviewRequest):
    """Custom text preview (max 100 chars)."""
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    if len(text) > 100:
        text = text[:100]

    try:
        communicate = edge_tts.Communicate(
            text, 
            request.voice, 
            rate=request.rate, 
            volume=request.volume, 
            pitch=request.pitch
        )
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="audio/mpeg")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@router.post("/preview")
async def preview_speech(request: PreviewRequest):
    """预览章节或文本"""
    # Logic from app.py
    import json
    
    text_to_speak = "这是一个语音预览测试。"
    
    # Check if we should fetch chapter text
    if request.book_name != "preview" and request.book_name != "voice_test" and request.chapter_id is not None:
        book_dir = APP_DATA_DIR / f"{request.book_name}_audio"
        tasks_file = book_dir / "tasks.json"
        if tasks_file.exists():
            try:
                with open(tasks_file, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
                for t in tasks:
                    if t['id'] == request.chapter_id:
                        content = t.get("content", "")
                        if content:
                            text_to_speak = content[:50]
                        break
            except:
                pass
    elif request.text:
        text_to_speak = request.text[:50]

    # Temp dir for preview
    temp_dir = APP_DATA_DIR / "temp_preview"
    temp_dir.mkdir(exist_ok=True)
    
    # Validate Params
    rate = request.config.rate
    if not rate.endswith("%"): rate += "%"
    
    volume = request.config.volume
    if not volume.endswith("%"): volume += "%"
    
    pitch = request.config.pitch if request.config.pitch else "+0Hz"
    if pitch and pitch != "0" and not pitch.endswith("Hz"): pitch += "Hz"

    processor = TTSProcessor(
        str(temp_dir),
        voice=request.config.voice,
        rate=rate,
        volume=volume,
        pitch=pitch,
        concurrency_limit=10 
    )
    
    try:
        audio_data = await processor.preview_speech(text_to_speak)
        return StreamingResponse(
            io.BytesIO(audio_data), 
            media_type="audio/mpeg"
        )
    except Exception as e:
        print(f"Preview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Bark 测试通知接口
from pydantic import BaseModel as PydanticBaseModel

class BarkTestRequest(PydanticBaseModel):
    server_url: str
    api_key: str

@router.post("/bark/test")
async def test_bark_notification(request: BarkTestRequest):
    """测试 Bark 推送配置"""
    from app.services.notifier import BarkNotifier
    
    # Get Bark configuration
    silent_hours_config = config.get_section("bark.silent_hours")
    http_timeout = config.get("bark.http_timeout", 5)
    
    notifier = BarkNotifier(
        server_url=request.server_url,
        api_key=request.api_key,
        enabled=True,
        web_base_url=WEB_BASE_URL,
        silent_hours_config=silent_hours_config,
        http_timeout=http_timeout
    )
    
    success = await notifier.send_test()
    
    if success:
        return {"success": True, "message": "测试通知发送成功！"}
    else:
        return {"success": False, "message": "测试通知发送失败，请检查配置"}
