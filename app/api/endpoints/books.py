
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

from app.core.config import APP_DATA_DIR, CACHE_DIR
from app.core.state import state
from app.services.book_manager import BookProcessor
from app.schemas.book import Book, Chapter
from app.schemas.config import GenerateRequest

router = APIRouter()

def get_book_status(book_dir: pathlib.Path, book_name: str):
    tasks_file = book_dir / "tasks.json"
    if not tasks_file.exists():
        return {"total": 0, "completed": 0, "status": "pending"}
    
    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        
        # Check if actually running
        is_running = book_name in state.active_processors
        
        if is_running:
            status = "processing"
        elif completed == total and total > 0:
            status = "completed"
        else:
            status = "pending" # Paused or not started
            
        return {"total": total, "completed": completed, "status": status}
    except Exception:
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
        
        return {"message": f"Successfully uploaded and processed {file.filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chapters/{book_name}")
async def list_chapters_api(book_name: str):
    book_dir = APP_DATA_DIR / f"{book_name}_audio"
    if not book_dir.exists():
        raise HTTPException(status_code=404, detail="Book not found")
        
    tasks_file = book_dir / "tasks.json"
    if not tasks_file.exists():
        return []

    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)
            # Return full details including length
            return [{
                "id": t.get("id"),
                "title": t.get("title"),
                "status": t.get("status", "pending"),
                "length": len(t.get("content", ""))
            } for t in tasks]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
from typing import List

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

    tasks_file = book_dir / "tasks.json"
    if not tasks_file.exists():
        return {"message": "No tasks file found"}

    try:
        # Load tasks
        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        
        updated = False
        target_ids = set(request.chapter_ids)
        
        for task in tasks:
            if task["id"] in target_ids:
                # 1. Reset status
                task["status"] = "pending"
                if "audio_path" in task:
                    del task["audio_path"]
                
                # 2. Delete file
                safe_title = str(task["title"]).replace("/", "_").replace("\\", "_")
                filename = f"{task['id']:04d}-{safe_title}.mp3"
                file_path = book_dir / filename
                if file_path.exists():
                    file_path.unlink()
                
                updated = True

        if updated:
            with open(tasks_file, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
                
        return {"message": f"Cleaned {len(target_ids)} chapters"}
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
