
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse
import shutil
import pathlib
import os
import json
import asyncio
import zipfile
import io
import subprocess
import logging

logger = logging.getLogger(__name__)

from app.core.config import APP_DATA_DIR, CACHE_DIR
from app.core.state import state
from app.services.book_manager import BookProcessor
from app.schemas.book import Book, Chapter
from app.schemas.config import GenerateRequest
from pydantic import BaseModel
from typing import List

router = APIRouter()

def get_book_status(book_dir: pathlib.Path, book_name: str):
    from app.db.database import db
    try:
        cursor = db.get_cursor()
        cursor.execute(
            "SELECT status, count(*) as count FROM tasks WHERE book_name = ? GROUP BY status", 
            (book_name,)
        )
        rows = cursor.fetchall()
        
        if not rows:
            # 可能是新书或者未导入 DB
            return {"total": 0, "completed": 0, "status": "pending"}

        stats = {row['status']: row['count'] for row in rows}
        total = sum(stats.values())
        completed = stats.get('completed', 0)
        
        # Check if actually running
        is_running = book_name in state.active_processors
        
        if is_running:
            status = "processing"
        elif completed == total and total > 0:
            status = "completed"
        else:
            status = "pending" # Paused or not started
            
        return {"total": total, "completed": completed, "status": status}
    except Exception as e:
        logger.error(f"Error getting book status: {e}")
        return {"total": 0, "completed": 0, "status": "error"}

@router.get("/books", response_model=None) # /api/books
async def list_books():
    books = []
    if not APP_DATA_DIR.exists():
        return []
        
    for item in APP_DATA_DIR.iterdir():
        if item.is_dir() and item.name.endswith("_audio"):
            book_name = item.name.replace("_audio", "")
            status_info = get_book_status(item, book_name)
            books.append({
                "name": book_name,
                "path": str(item),
                **status_info
            })
    return books

@router.post("/upload")
async def upload_book(file: UploadFile = File(...)):
    file_path = APP_DATA_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process book immediately
        processor = BookProcessor(str(file_path))
        await asyncio.to_thread(processor.process)
        
        logger.info(f"📚 Book uploaded and processed: {file.filename}")
        
        return {"message": f"Successfully uploaded and processed {file.filename}"}
    except Exception as e:
        logger.error(f"Upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/books/{book_name}")
async def delete_book(book_name: str):
    """删除书籍及其所有文件"""
    # 1. 检查是否正在运行
    if book_name in state.active_processors:
        raise HTTPException(status_code=400, detail="Cannot delete book while processing. Please stop the task first.")
    
    # 2. 删除数据库记录
    from app.db.database import db
    try:
        db.delete_book_tasks(book_name)
    except Exception as e:
        # 记录错误但继续尝试删除文件
        logger.error(f"Error deleting DB records for {book_name}: {e}")

    # 3. 删除文件目录
    book_dir = APP_DATA_DIR / f"{book_name}_audio"
    if book_dir.exists():
        try:
            shutil.rmtree(book_dir)
        except Exception as e:
            logger.error(f"Failed to delete book directory for {book_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete book directory: {e}")

    # 4. 删除源文件 (txt/epub)
    # 遍历 APP_DATA_DIR 找到同名文件 (忽略扩展名)
    try:
        for item in APP_DATA_DIR.iterdir():
            if item.is_file() and item.stem == book_name:
                # 排除数据库文件和配置文件，防止误删 (虽然一般名字对不上)
                if item.suffix.lower() in ['.db', '.sql', '.log', '.yml', '.yaml', '.json']:
                    continue
                
                try:
                    item.unlink()
                    logger.info(f"Deleted source file: {item.name}")
                except Exception as e:
                    logger.error(f"Failed to delete source file {item.name}: {e}")
    except Exception as e:
         logger.error(f"Error scanning for source files: {e}")
            
    logger.info(f"🗑️ Book deleted: {book_name}")
    return {"message": f"Book '{book_name}' deleted successfully"}

@router.get("/chapters/{book_name}")
async def list_chapters_api(book_name: str):
    book_dir = APP_DATA_DIR / f"{book_name}_audio"
    if not book_dir.exists():
        # 如果目录不存在，检查数据库（可能目录被删了但库还在？）
        # 这里还是保持一致性，如果文件夹不在也不应该有任务
        raise HTTPException(status_code=404, detail="Book not found")
        
    from app.db.database import db
    try:
        cursor = db.get_cursor()
        cursor.execute("SELECT * FROM tasks WHERE book_name = ? ORDER BY chapter_index", (book_name,))
        rows = cursor.fetchall()
        
        if not rows:
             return []

        # Return full details
        return [{
            "id": row['chapter_index'], # 注意：DB里的 id 是 string ID，前端可能期待 int index
            "title": row['title'],
            "status": row['status'],
            "length": len(row['content']) if row['content'] else 0
        } for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CleanRequest(BaseModel):
    chapter_ids: List[int]

@router.post("/clean/{book_name}")
async def clean_chapters(book_name: str, request: CleanRequest):
    book_dir = APP_DATA_DIR / f"{book_name}_audio"
    if not book_dir.exists():
         raise HTTPException(status_code=404, detail="Book not found")
         
    # Check if running
    if book_name in state.active_processors:
        raise HTTPException(status_code=400, detail="Cannot clean while task is running. Please pause or stop first.")

    from app.db.database import db
    try:
        conn = db.conn
        if not conn:
            db.connect()
            conn = db.conn
            
        cursor = conn.cursor()
        
        # 1. 查找需要清理的任务以获取文件名
        placeholders = ','.join(['?'] * len(request.chapter_ids))
        query = f"SELECT chapter_index, title, audio_path FROM tasks WHERE book_name = ? AND chapter_index IN ({placeholders})"
        cursor.execute(query, (book_name, *request.chapter_ids))
        rows = cursor.fetchall()
        
        if not rows:
            return {"message": "No matching chapters found"}

        cleaned_count = 0
        for row in rows:
            # Delete file
            # 优先使用数据库记录的路径
            if row['audio_path']:
                file_path = book_dir / row['audio_path']
                if file_path.exists():
                    file_path.unlink()
            else:
                # 备用方案: 构造文件名
                safe_title = str(row['title']).replace("/", "_").replace("\\", "_")
                filename = f"{row['chapter_index']:04d}-{safe_title}.mp3"
                file_path = book_dir / filename
                if file_path.exists():
                     file_path.unlink()

            cleaned_count += 1
            
        # 2. Reset status in DB
        update_query = f"UPDATE tasks SET status = 'pending', audio_path = NULL WHERE book_name = ? AND chapter_index IN ({placeholders})"
        cursor.execute(update_query, (book_name, *request.chapter_ids))
        conn.commit()
                
        return {"message": f"Cleaned {cleaned_count} chapters"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open_folder")
async def open_folder_api(book_name: str = Query(...)):
    path = APP_DATA_DIR / f"{book_name}_audio"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
        
    import platform
    
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", str(path)])
        else:  # Linux
            subprocess.Popen(["xdg-open", str(path)])
        return {"message": "Folder opened"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files/{book_name}")
async def list_audio_files(book_name: str):
    """获取书籍的所有音频文件列表"""
    book_dir = APP_DATA_DIR / f"{book_name}_audio"
    if not book_dir.exists():
        raise HTTPException(status_code=404, detail="Book not found")
    
    files = []
    for mp3_file in sorted(book_dir.glob("*.mp3")):
        try:
            # 解析文件名: 0001-章节标题.mp3
            parts = mp3_file.name.split('-', 1)
            if len(parts) >= 1:
                file_id = int(parts[0])
                file_size = mp3_file.stat().st_size
                
                files.append({
                    "id": file_id,
                    "filename": mp3_file.name,
                    "size": file_size,
                    "path": mp3_file.name
                })
        except (ValueError, IndexError):
            # Skip files that don't match the expected format
            continue
    
    return files

@router.get("/file/{book_name}/{file_id}")
async def download_single_file(book_name: str, file_id: int):
    """下载单个音频文件"""
    book_dir = APP_DATA_DIR / f"{book_name}_audio"
    if not book_dir.exists():
        raise HTTPException(status_code=404, detail="Book not found")
    
    # 查找匹配的文件
    for mp3_file in book_dir.glob(f"{file_id:04d}-*.mp3"):
        return FileResponse(
            mp3_file,
            filename=mp3_file.name,
            media_type="audio/mpeg"
        )
    
    raise HTTPException(status_code=404, detail="File not found")

@router.get("/download/{book_name}")
async def download_book_audio(book_name: str):
    """打包下载音频"""
    # Locate book dir
    target_dir = APP_DATA_DIR / f"{book_name}_audio"
            
    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Book directory not found")
        
    # Create zip in memory
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".mp3"):
                    file_path = os.path.join(root, file)
                    zip_file.write(file_path, arcname=file)
                    
    buffer.seek(0)
    return StreamingResponse(
        buffer, 
        media_type="application/zip", 
        headers={"Content-Disposition": f"attachment; filename={book_name}.zip"}
    )

@router.post("/merge/{book_name}")
async def merge_audio(book_name: str, request: GenerateRequest): 
    """合并音频"""
    target_dir = APP_DATA_DIR / f"{book_name}_audio"
            
    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Book directory not found")
        
    # Filter chapters if provided
    chapter_ids = request.chapter_ids
    
    # Get all mp3 files
    mp3_files = sorted([f for f in target_dir.glob("*.mp3")])
    if not mp3_files:
        raise HTTPException(status_code=400, detail="No audio files to merge")
        
    # If specific chapters requested, filter them
    if chapter_ids:
        filtered_files = []
        for f in mp3_files:
            try:
                # Extract ID from filename start "0001"
                fid = int(f.name.split('-')[0])
                if fid in chapter_ids:
                    filtered_files.append(f)
            except:
                pass
        mp3_files = filtered_files
        
    if not mp3_files:
        raise HTTPException(status_code=400, detail="No matching audio files for selected chapters")

    # Create filelist for ffmpeg
    list_path = target_dir / "filelist.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for mp3 in mp3_files:
            safe_path = str(mp3.absolute()).replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    output_path = target_dir / f"{book_name}_merged.mp3"
    
    try:
        cmd = [
            "ffmpeg", "-y", 
            "-f", "concat", 
            "-safe", "0", 
            "-i", str(list_path), 
            "-c", "copy", 
            str(output_path)
        ]
        # Run in thread to not block event loop
        await asyncio.to_thread(subprocess.check_call, cmd)
        
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ffmpeg not installed on server")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"ffmpeg merge failed: {e}")
    finally:
        if list_path.exists():
            list_path.unlink()
            
    return FileResponse(output_path, filename=f"{book_name}_merged.mp3")
