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
    检查所有版本更新 (Engine + App)
    """
    if not version_checker.checking:
        background_tasks.add_task(version_checker.check_update)
    
    status = version_checker.get_status()
    
    return {
        "checking": version_checker.checking,
        **status
    }


@router.get("/version/info")
async def get_version_info():
    """
    获取当前版本详情
    """
    status = version_checker.get_status()
    return status


@router.post("/version/dismiss")
async def dismiss_update():
    """
    忽略当前更新提示
    """
    version_checker.clear_update_info()
    return {"success": True}
