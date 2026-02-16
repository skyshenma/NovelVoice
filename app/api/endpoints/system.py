from fastapi import APIRouter
import shutil
from app.core.config import DATA_DIR

router = APIRouter()

@router.get("/storage")
async def get_system_storage():
    """
    Get system storage usage information for the data directory.
    """
    try:
        total, used, free = shutil.disk_usage(DATA_DIR)
        percent = (used / total) * 100
        return {
            "total": total,
            "used": used,
            "free": free,
            "percent": round(percent, 2)
        }
    except Exception as e:
        return {
            "total": 0,
            "used": 0,
            "free": 0,
            "percent": 0,
            "error": str(e)
        }
