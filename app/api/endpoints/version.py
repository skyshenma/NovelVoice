"""
版本检查 API 端点
提供版本信息查询和更新检查功能
"""

from fastapi import APIRouter, BackgroundTasks
from app.services.version_checker import version_checker

router = APIRouter()


@router.get("/version/check")
async def check_version(background_tasks: BackgroundTasks):
    """
    检查版本更新
    
    后台异步检查,立即返回当前状态
    
    Returns:
        {
            "checking": bool,           # 是否正在检查
            "update_available": bool,   # 是否有更新
            "update_info": dict | null  # 更新信息
        }
    """
    # 如果没有正在检查,启动后台检查
    if not version_checker.checking:
        background_tasks.add_task(version_checker.check_update, "edge-tts")
    
    # 返回当前更新信息
    update_info = version_checker.get_update_info()
    
    return {
        "checking": version_checker.checking,
        "update_available": update_info is not None,
        "update_info": update_info
    }


@router.get("/version/info")
async def get_version_info():
    """
    获取版本信息
    
    Returns:
        {
            "current_version": str,     # 当前版本
            "update_available": bool,   # 是否有更新
            "update_info": dict | null  # 更新信息
        }
    """
    current = version_checker.get_installed_version("edge-tts")
    update_info = version_checker.get_update_info()
    
    return {
        "current_version": current,
        "update_available": update_info is not None,
        "update_info": update_info
    }


@router.post("/version/dismiss")
async def dismiss_update():
    """
    忽略当前更新提示
    
    Returns:
        {"success": bool}
    """
    version_checker.clear_update_info()
    return {"success": True}
