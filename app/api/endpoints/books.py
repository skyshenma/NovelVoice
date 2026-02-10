import time
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
import threading
import shutil
import re

logger = logging.getLogger(__name__)

from app.core.config import APP_DATA_DIR, CACHE_DIR, EXPORT_DIR
from app.core.state import state
from app.core.log_manager import log_manager
from app.services.book_manager import BookProcessor
from app.schemas.book import Book, Chapter
from app.schemas.config import GenerateRequest
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

def get_book_dir(book_name: str) -> pathlib.Path:
    """获取书籍音频目录，处理末尾空格的兼容性"""
    # 1. 尝试完全匹配
    path = APP_DATA_DIR / f"{book_name}_audio"
    if path.exists():
        return path
        
    # 2. 如果不匹配，尝试修剪 (trim) 后的匹配
    trimmed_name = book_name.strip()
    if trimmed_name != book_name:
        path = APP_DATA_DIR / f"{trimmed_name}_audio"
        if path.exists():
            return path
            
    # 3. 实在找不到，返回常规路径（即使不存在）
    return APP_DATA_DIR / f"{book_name}_audio"

def get_book_status(book_name: str):
    from app.db.database import db
    book_dir = get_book_dir(book_name)
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
            
    
        # Check zip status from DB
        zip_assets = []
        cursor.execute(
            "SELECT id, filename, description, size_str, created_at FROM book_assets WHERE book_name = ? ORDER BY created_at DESC",
            (book_name,)
        )
        asset_rows = cursor.fetchall()
        for row in asset_rows:
            # Verify file exists on disk
            asset_path = EXPORT_DIR / row['filename']
            if asset_path.exists():
                zip_assets.append({
                    "id": row['id'],
                    "filename": row['filename'],
                    "description": row['description'],
                    "size": row['size_str'],
                    "created_at": row['created_at']
                })
            else:
                # Optionally cleanup missing files from DB
                cursor.execute("DELETE FROM book_assets WHERE id = ?", (row['id'],))
        db.commit()

        zip_status = "none"
        if book_name in state.active_packers:
            zip_status = state.active_packers[book_name]
        elif zip_assets:
            zip_status = "ready"

        return {
            "total": total, 
            "completed": completed, 
            "status": status, 
            "zip_status": zip_status,
            "zip_assets": zip_assets
        }
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
            # Trim book_name to remove potential trailing spaces from filesystem
            book_name = item.name.replace("_audio", "").strip()
            status_info = get_book_status(book_name)
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
    book_dir = get_book_dir(book_name)
    if book_dir.exists():
        try:
            shutil.rmtree(book_dir)
        except Exception as e:
            logger.error(f"Failed to delete book directory for {book_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete book directory: {e}")

    # 3.5 删除所有相关资产 (zip)
    try:
        zip_path = EXPORT_DIR / f"{book_name}.zip"
        if zip_path.exists():
            zip_path.unlink()
            logger.info(f"Deleted zip asset for {book_name}")
    except Exception as e:
        logger.error(f"Failed to delete zip asset for {book_name}: {e}")

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
    book_dir = get_book_dir(book_name)
    if not book_dir.exists():
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
            "id": row['chapter_index'],
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
    book_dir = get_book_dir(book_name)
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
            if row['audio_path']:
                file_path = book_dir / row['audio_path']
                if file_path.exists():
                    file_path.unlink()
            else:
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
    path = get_book_dir(book_name)
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
    book_dir = get_book_dir(book_name)
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
    book_dir = get_book_dir(book_name)
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

    
    raise HTTPException(status_code=404, detail="File not found")

def check_disk_space(target_dir: pathlib.Path, min_mb: int = 500):
    """Ensure sufficient disk space (default 500MB)"""
    try:
        total, used, free = shutil.disk_usage(target_dir)
        if free < min_mb * 1024 * 1024:
            raise Exception(f"磁盘空间不足! 需要 {min_mb}MB, 剩余 {free // (1024*1024)}MB")
    except Exception as e:
        logger.error(f"Disk check failed: {e}")
        raise e

def sanitize_filename(name: str) -> str:
    """Sanitize filename to prevent path traversal and shell injection"""
    # Remove dangerous characters
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip()
    # Ensure it's not empty or just dots
    if not name or name.replace(".", "") == "":
        name = "unnamed_file"
    return name

def pack_book_task(book_name: str, target_dir: pathlib.Path, cancel_event: threading.Event, description: str = "Full Pack", file_ids: Optional[List[int]] = None):
    """Background task for packing book audio with cancellation support and unique naming"""
    temp_zip_path = None
    try:
        # [Patch] Disk Check
        check_disk_space(EXPORT_DIR)

        # Check if dir exists
        if not target_dir.exists():
            logger.error(f"📚 Book dir not found for packing: {book_name}")
            return
            
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        
        # [Patch] Filename Safety & Uniqueness
        safe_book_name = sanitize_filename(book_name)
        
        # Determine dynamic filename based on description (e.g., "Chapters: 1-10" -> "1-10")
        range_label = "Full"
        if description.startswith("Chapters:"):
            range_label = description.replace("Chapters:", "").strip().replace(" ", "")
        elif description.startswith("Range:"):
            range_label = description.replace("Range:", "").strip().replace(" ", "")
        elif description.startswith("Files:"):
            # Try to get cleaner range if it looks like "1,2,3"
            files_str = description.replace("Files:", "").strip()
            if "," in files_str:
                parts = [p.strip() for p in files_str.split(',')]
                if len(parts) > 2:
                    range_label = f"{parts[0]}-{parts[-1]}"
                else:
                    range_label = files_str.replace(",", "-")
            else:
                range_label = files_str
        
        if not range_label or range_label == "Selected":
            range_label = "Pack"

        # Clean range label for filename safety
        safe_range = sanitize_filename(range_label)
        file_basename = f"{safe_book_name}_{safe_range}.zip"
        
        # Use timestamp for temp file to ensure unique background operations
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        temp_zip_path = EXPORT_DIR / f"{safe_book_name}_temp_{timestamp}.zip"
        final_zip_path = EXPORT_DIR / file_basename

        # 1. Collect files
        # ... (scanning logic remains same)
        files_to_zip = []
        for root, dirs, files in os.walk(target_dir):
            if cancel_event.is_set():
                raise asyncio.CancelledError("Task cancelled during file scanning")
                
            for file in files:
                if file.endswith(".mp3"):
                    # Check if we should filter by ID
                    # Our files are named like "001_Title.mp3", id is usually extracted
                    file_path = os.path.join(root, file)
                    arcname = sanitize_filename(file)
                    
                    if file_ids is not None:
                        # Improved fid extraction: handle 0001-Title.mp3 or 001_Title.mp3
                        try:
                            match = re.match(r'^(\d+)', file)
                            if match:
                                fid = int(match.group(1))
                                if fid not in file_ids:
                                    continue
                            else:
                                # If no leading digits, only include if not filtering
                                continue
                        except (ValueError, IndexError):
                            if description != "Full Pack":
                                continue
                                
                    files_to_zip.append((file_path, arcname))
        
        total_files = len(files_to_zip)
        logger.info(f"📦 开始打包 '{book_name}' [{description}] (共 {total_files} 个文件)...")
        log_manager.put_log(f"📦 开始打包 '{book_name}' [{description}] (共 {total_files} 个文件)...")

        # 2. Write zip
        with zipfile.ZipFile(temp_zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) as zip_file:
            for i, (file_path, arcname) in enumerate(files_to_zip):
                if cancel_event.is_set():
                    raise asyncio.CancelledError("Task cancelled during zipping")
                
                with open(file_path, 'rb') as src_file:
                    with zip_file.open(arcname, 'w') as dest_file:
                        while True:
                            if cancel_event.is_set():
                                raise asyncio.CancelledError("Task cancelled inner loop")
                            chunk = src_file.read(1024 * 1024)
                            if not chunk: break
                            dest_file.write(chunk)
                
                if total_files > 0 and (i + 1) % max(1, total_files // 20) == 0:
                    percent = int((i + 1) / total_files * 100)
                    log_manager.put_log(f"📦 '{book_name}' 打包进度: {percent}% ({i + 1}/{total_files})")

        # Move to final and register in DB
        if temp_zip_path.exists():
            if cancel_event.is_set():
                 raise asyncio.CancelledError("Task cancelled before finalize")

            if final_zip_path.exists():
                try:
                    final_zip_path.unlink()
                except Exception as e:
                    logger.warning(f"Could not remove existing zip {final_zip_path}: {e}")

            temp_zip_path.rename(final_zip_path)
            
            # Register asset in DB
            from app.db.database import db
            size_bytes = final_zip_path.stat().st_size
            if size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f}KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f}MB"
            
            cursor = db.get_cursor()
            cursor.execute(
                "INSERT INTO book_assets (book_name, filename, description, size_str) VALUES (?, ?, ?, ?)",
                (book_name, file_basename, description, size_str)
            )
            db.commit()
            
        logger.info(f"✅ '{book_name}' 打包完成: {file_basename}")
        log_manager.put_log(f"✅ '{book_name}' 打包完成 [{description}]。")

    except asyncio.CancelledError:
        logger.warning(f"🚫 打包任务已取消: {book_name}")
        log_manager.put_log(f"🚫 打包任务已取消: {book_name}")
        # Cleanup happens in finally block
    except Exception as e:
        logger.error(f"❌ 打包 '{book_name}' 失败: {e}")
        log_manager.put_log(f"❌ 打包 '{book_name}' 失败: {e}")
    finally:
        # Cleanup temp file
        if temp_zip_path and temp_zip_path.exists():
            try:
                temp_zip_path.unlink()
                logger.info(f"🧹 已清理临时文件: {temp_zip_path}")
            except Exception as e:
                logger.error(f"清理临时文件失败: {e}")

        # Reset state
        if book_name in state.active_packers:
            del state.active_packers[book_name]
        if book_name in state.cancel_events:
            del state.cancel_events[book_name]


@router.post("/pack/{book_name}", status_code=202)
async def pack_book_endpoint(
    book_name: str, 
    background_tasks: BackgroundTasks, 
    description: str = "Full Pack",
    file_ids: Optional[str] = Query(None) # Pass as comma separated string
):
    """Start packing book audio"""
    logger.info(f"📥 Pack request: {book_name}, Desc: {description}, IDs: {file_ids}")
    parsed_ids = None
    if file_ids:
        try:
            parsed_ids = [int(x.strip()) for x in file_ids.split(",") if x.strip()]
            logger.info(f"🔢 Parsed IDs: {parsed_ids}")
        except ValueError:
            logger.error(f"❌ Invalid file_ids: {file_ids}")
            raise HTTPException(status_code=400, detail="Invalid file_ids format")

    if book_name in state.active_packers:
        # Check if cancelling
        if state.active_packers[book_name] == "cancelling":
             raise HTTPException(status_code=400, detail="Previous task is cancelling, please wait")
        raise HTTPException(status_code=400, detail="Packing task already in progress")
        
    target_dir = get_book_dir(book_name)
    if not target_dir.exists():
        raise HTTPException(status_code=404, detail="Book directory not found")
        
    # Init cancellation event
    cancel_event = threading.Event()
    state.cancel_events[book_name] = cancel_event

    # Set state
    state.active_packers[book_name] = "packing"
    
    # Start task
    background_tasks.add_task(pack_book_task, book_name, target_dir, cancel_event, description, parsed_ids)
    
    return {"message": "Packing task started", "status": "packing"}

@router.post("/pack/cancel/{book_name}")
async def cancel_pack_endpoint(book_name: str):
    """Cancel packing task"""
    if book_name not in state.active_packers:
        raise HTTPException(status_code=404, detail="No active packing task found")
    
    if book_name in state.cancel_events:
        state.cancel_events[book_name].set()
        state.active_packers[book_name] = "cancelling"
        log_manager.put_log(f"🛑 正在中止 '{book_name}' 的打包任务...")
        return {"message": "Cancellation requested", "status": "cancelling"}
    
    return {"message": "Task not cancellable or already finished"}

@router.get("/assets/download/{asset_id}")
async def download_asset(asset_id: int):
    """Download specific asset by ID"""
    from app.db.database import db
    cursor = db.get_cursor()
    cursor.execute("SELECT filename, book_name FROM book_assets WHERE id = ?", (asset_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    zip_path = EXPORT_DIR / row['filename']
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Physical file missing")
        
    return FileResponse(
        zip_path, 
        media_type="application/zip", 
        filename=row['filename']
    )

@router.get("/download_zip/{book_name}")
async def download_book_zip(book_name: str):
    """Download the LATEST packed zip for a book"""
    from app.db.database import db
    cursor = db.get_cursor()
    cursor.execute(
        "SELECT id, filename FROM book_assets WHERE book_name = ? ORDER BY created_at DESC LIMIT 1",
        (book_name,)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No zip files found for this book")
    
    return await download_asset(row['id'])

@router.delete("/zip/{book_name}")
async def delete_book_zip(book_name: str, asset_id: Optional[int] = Query(None)):
    """Delete packed zip (specific asset or all)"""
    from app.db.database import db
    cursor = db.get_cursor()
    
    if asset_id:
        cursor.execute("SELECT filename FROM book_assets WHERE id = ? AND book_name = ?", (asset_id, book_name))
        row = cursor.fetchone()
        if row:
            filepath = EXPORT_DIR / row['filename']
            if filepath.exists(): filepath.unlink()
            cursor.execute("DELETE FROM book_assets WHERE id = ?", (asset_id,))
            db.commit()
            return {"message": f"Asset {asset_id} deleted"}
        raise HTTPException(status_code=404, detail="Asset not found")
    else:
        # Delete ALL assets for this book
        cursor.execute("SELECT filename FROM book_assets WHERE book_name = ?", (book_name,))
        rows = cursor.fetchall()
        for row in rows:
            filepath = EXPORT_DIR / row['filename']
            if filepath.exists(): filepath.unlink()
        
        cursor.execute("DELETE FROM book_assets WHERE book_name = ?", (book_name,))
        db.commit()
        return {"message": "All zip assets for this book deleted"}

@router.post("/merge/{book_name}")
async def merge_audio(book_name: str, request: GenerateRequest): 
    """合并音频"""
    target_dir = get_book_dir(book_name)
            
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
        
        logger.info(f"🔗 开始合并 '{book_name}' 的音频 (共 {len(mp3_files)} 个文件)...")

        # Run in thread to not block event loop
        await asyncio.to_thread(subprocess.check_call, cmd)
        
        logger.info(f"✅ 音频合并完成: {output_path.name}")
        
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ffmpeg not installed on server")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"ffmpeg merge failed: {e}")
    finally:
        if list_path.exists():
            list_path.unlink()
            
    return FileResponse(output_path, filename=f"{book_name}_merged.mp3")
