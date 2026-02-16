from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional
from pydantic import BaseModel
import shutil
import pathlib
import os
import logging
import re
from app.core.config import APP_DATA_DIR, EXPORT_DIR
from app.api.endpoints.books import get_book_dir, sanitize_filename

router = APIRouter()
logger = logging.getLogger(__name__)

class FileItem(BaseModel):
    name: str # Filename
    path: str # Relative path or identifier
    size: int
    type: str # 'audio' | 'zip' | 'other'
    book_name: Optional[str] = None # If associated with a book
    created_at: float

class FileSummary(BaseModel):
    books: List[dict] # {name: "book1", file_count: 10, total_size: 102400}
    exports: List[FileItem] # ZIP files in export dir
    total_size: int

def is_safe_path(target_path: pathlib.Path, allowed_roots: List[pathlib.Path]) -> bool:
    """
    Security check: Ensure target_path is within one of the allowed_roots.
    Prevents path traversal attacks (e.g. ../../../etc/passwd).
    """
    try:
        resolved_target = target_path.resolve()
        for root in allowed_roots:
            resolved_root = root.resolve()
            # method 1: use pathlib.is_relative_to (python 3.9+)
            if hasattr(resolved_target, 'is_relative_to'):
                 if resolved_target.is_relative_to(resolved_root):
                     return True
            else:
                 # method 2: string comparison for older python
                 if str(resolved_target).startswith(str(resolved_root)):
                     return True
        return False
    except Exception as e:
        logger.error(f"Path security check failed: {e}")
        return False

@router.get("/summary", response_model=FileSummary)
async def get_files_summary():
    """
    Get a global summary of all files managed by the system.
    Includes:
    1. Books and their audio file stats
    2. Exported ZIP files
    """
    summary = {
        "books": [],
        "exports": [],
        "total_size": 0
    }
    
    # 1. Scan Books
    if APP_DATA_DIR.exists():
        for item in APP_DATA_DIR.iterdir():
            if item.is_dir() and item.name.endswith("_audio"):
                book_name = item.name.replace("_audio", "")
                
                # Count mp3s
                mp3s = list(item.glob("*.mp3"))
                size = sum(f.stat().st_size for f in mp3s)
                
                summary["books"].append({
                    "id": book_name,
                    "name": book_name,
                    "title": book_name, # Map directory name to title for now
                    "file_count": len(mp3s),
                    "total_size": size
                })
                summary["total_size"] += size

    # 2. Scan Exports
    if EXPORT_DIR.exists():
        for item in EXPORT_DIR.iterdir():
            if item.is_file() and item.name.endswith(".zip"):
                 size = item.stat().st_size
                 summary["exports"].append({
                     "name": item.name,
                     "path": item.name, 
                     "size": size,
                     "type": "zip",
                     "created_at": item.stat().st_mtime
                 })
                 summary["total_size"] += size
                 
    # Sort exports by new
    summary["exports"].sort(key=lambda x: x['created_at'], reverse=True)
    
    return summary

@router.delete("/delete")
async def delete_file(
    path: str = Query(..., description="Relative path of file to delete (e.g. 'book_name/001.mp3' or 'export.zip')"),
    type: str = Query(..., description="'book_file' or 'export_file'")
):
    """
    Securely delete a file.
    """
    target_path = None
    
    if type == "export_file":
        # Delete from EXPORT_DIR
        safe_name = sanitize_filename(path)
        target_path = EXPORT_DIR / safe_name
        
        # Security check: MUST be in EXPORT_DIR
        if not is_safe_path(target_path, [EXPORT_DIR]):
             raise HTTPException(status_code=403, detail="Access denied: Invalid export file path")

    elif type == "book_file":
        # Delete from APP_DATA_DIR (e.g. Audio files)
        # Expected format: "BookName/Filename.mp3"
        parts = path.split('/')
        if len(parts) != 2:
             raise HTTPException(status_code=400, detail="Invalid path format for book file")
             
        book_name = sanitize_filename(parts[0])
        filename = sanitize_filename(parts[1])
        book_dir = get_book_dir(book_name)
        target_path = book_dir / filename
        
        # Security check: MUST be in APP_DATA_DIR
        if not is_safe_path(target_path, [APP_DATA_DIR]):
             raise HTTPException(status_code=403, detail="Access denied: Invalid book file path")
             
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

    if not target_path or not target_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        target_path.unlink()
        logger.info(f"🗑️ Deleted file via API: {target_path}")
        
        # If it was a zip from assets, try to clean DB record too
        if type == "export_file":
             from app.db.database import db
             try:
                 cursor = db.get_cursor()
                 cursor.execute("DELETE FROM book_assets WHERE filename = ?", (path,))
                 db.commit()
             except Exception:
                 pass # Ignore DB errors if file is gone
                 
        return {"message": "File deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete file {target_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.get("/download/export")
async def download_export_file(filename: str = Query(...)):
    """Download export file by filename"""
    safe_name = sanitize_filename(filename)
    file_path = EXPORT_DIR / safe_name
    
    # Security check
    if not is_safe_path(file_path, [EXPORT_DIR]):
         raise HTTPException(status_code=403, detail="Access denied")
         
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(
        file_path, 
        filename=safe_name, 
        media_type="application/zip"
    )
