"""
配置管理 API 端点
提供配置的读取和保存功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any

from app.core.config_loader import (
    get_config, 
    save_config_to_yaml, 
    validate_tts_config
)

router = APIRouter()


# ==================== 数据模型 ====================

class TTSConfigUpdate(BaseModel):
    """TTS 配置更新模型"""
    default_voice: Optional[str] = None
    default_rate: Optional[str] = None
    default_volume: Optional[str] = None
    default_pitch: Optional[str] = None
    concurrency_limit: Optional[int] = Field(None, ge=1, le=10, description="并发数 (1-10)")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="重试次数 (0-10)")
    timeout: Optional[int] = Field(None, ge=10, le=120, description="超时时间 (10-120秒)")
    max_chars: Optional[int] = Field(None, ge=1000, le=20000, description="最大字符数")
    
    @validator('default_rate')
    def validate_rate(cls, v):
        if v:
            try:
                val = int(v.replace('%', '').replace('+', '').replace('-', ''))
                if not (-50 <= val <= 100):
                    raise ValueError('语速必须在 -50% 到 +100% 之间')
            except (ValueError, AttributeError):
                raise ValueError('语速格式错误,应为 "+0%" 格式')
        return v
    
    @validator('default_volume')
    def validate_volume(cls, v):
        if v:
            try:
                val = int(v.replace('%', '').replace('+', '').replace('-', ''))
                if not (-50 <= val <= 50):
                    raise ValueError('音量必须在 -50% 到 +50% 之间')
            except (ValueError, AttributeError):
                raise ValueError('音量格式错误,应为 "+0%" 格式')
        return v
    
    @validator('default_pitch')
    def validate_pitch(cls, v):
        if v:
            try:
                val = int(v.replace('Hz', '').replace('+', '').replace('-', ''))
                if not (-50 <= val <= 50):
                    raise ValueError('音调必须在 -50Hz 到 +50Hz 之间')
            except (ValueError, AttributeError):
                raise ValueError('音调格式错误,应为 "+0Hz" 格式')
        return v


class BarkConfigUpdate(BaseModel):
    """Bark 通知配置更新模型"""
    enabled: Optional[bool] = None
    server_url: Optional[str] = None
    api_key: Optional[str] = None
    web_base_url: Optional[str] = None


class ServerConfigUpdate(BaseModel):
    """服务器配置更新模型"""
    host: Optional[str] = None
    port: Optional[int] = Field(None, ge=1, le=65535, description="端口号 (1-65535)")
    reload: Optional[bool] = None


class ConfigUpdateRequest(BaseModel):
    """配置更新请求模型"""
    tts: Optional[TTSConfigUpdate] = None
    bark: Optional[BarkConfigUpdate] = None
    server: Optional[ServerConfigUpdate] = None


# ==================== API 端点 ====================

@router.get("/config")
async def get_current_config():
    """
    获取当前配置
    
    返回 config.yml 中的所有配置项
    """
    try:
        config = get_config()
        return {
            "success": True,
            "config": {
                "tts": config.get_section("tts"),
                "bark": config.get_section("bark"),
                "server": config.get_section("server"),
                "text_processing": config.get_section("text_processing"),
                "paths": config.get_section("paths"),
                "logging": config.get_section("logging"),
                "voices": config.get_section("voices")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.post("/config")
async def update_config(request: ConfigUpdateRequest):
    """
    更新配置并保存到 config.yml
    
    只更新提交的字段,未提交的字段保持不变
    """
    try:
        # 构建更新字典
        updates = {}
        
        if request.tts:
            tts_dict = request.tts.dict(exclude_none=True)
            if tts_dict:
                # 额外验证
                errors = validate_tts_config(tts_dict)
                if errors:
                    raise HTTPException(
                        status_code=400, 
                        detail={"message": "参数验证失败", "errors": errors}
                    )
                updates["tts"] = tts_dict
        
        if request.bark:
            bark_dict = request.bark.dict(exclude_none=True)
            if bark_dict:
                updates["bark"] = bark_dict
        
        if request.server:
            server_dict = request.server.dict(exclude_none=True)
            if server_dict:
                updates["server"] = server_dict
        
        if not updates:
            raise HTTPException(status_code=400, detail="没有要更新的配置项")
        
        # 保存配置
        success = save_config_to_yaml(updates)
        
        if success:
            return {
                "success": True,
                "message": "配置已保存",
                "updated": updates
            }
        else:
            raise HTTPException(status_code=500, detail="保存配置失败")
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.post("/config/validate")
async def validate_config(config: Dict[str, Any]):
    """
    验证配置参数(不保存)
    
    用于前端实时验证
    """
    try:
        errors = {}
        
        if "tts" in config:
            tts_errors = validate_tts_config(config["tts"])
            if tts_errors:
                errors["tts"] = tts_errors
        
        if errors:
            return {
                "valid": False,
                "errors": errors
            }
        else:
            return {
                "valid": True,
                "message": "配置参数有效"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


@router.post("/config/reload")
async def reload_config():
    """
    重新加载配置文件
    
    从磁盘重新读取 config.yml 并更新内存配置
    """
    try:
        config = get_config()
        result = await config.reload()
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "config": {
                    "tts": result["config"].get("tts", {}),
                    "bark": result["config"].get("bark", {}),
                    "server": result["config"].get("server", {}),
                    "text_processing": result["config"].get("text_processing", {}),
                    "paths": result["config"].get("paths", {}),
                    "logging": result["config"].get("logging", {}),
                    "voices": result["config"].get("voices", [])
                },
                "changes": result.get("changes", {})
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"重载配置失败: {str(e)}")
