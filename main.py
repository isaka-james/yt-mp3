from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import yt_dlp
import os
import asyncio
from typing import Optional, List
import json
import uuid
import zipfile
import io
import logging
from datetime import datetime
import re

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose logs
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler('app.log')  # File handler for persistence
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="YouTube MP3 Downloader")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create downloads directory
DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
logger.info(f"Downloads directory created/verified: {DOWNLOADS_DIR}")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info("Static files mounted at /static")

class DownloadRequest(BaseModel):
    url: HttpUrl

class VideoInfo(BaseModel):
    title: str
    duration: int
    thumbnail: str
    uploader: str

# Store download progress
download_progress = {}
logger.info("Application initialized and ready")

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def progress_hook(d, task_id, video_index=None, total_videos=None):
    """Hook to track download progress"""
    logger.debug(f"Progress hook called: {d['status']} for task {task_id}")
    
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        
        if total > 0:
            percentage = (downloaded / total) * 100
            
            # Calculate overall progress for playlists
            if video_index is not None and total_videos is not None:
                # Each video represents a portion of the total progress
                video_progress = ((video_index - 1) / total_videos) * 100
                current_video_progress = (percentage / total_videos)
                overall_percentage = video_progress + current_video_progress
            else:
                overall_percentage = percentage
            
            progress_data = {
                'status': 'downloading',
                'percentage': round(overall_percentage, 1),
                'downloaded': downloaded,
                'total': total,
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0)
            }
            
            if video_index is not None:
                progress_data['current_video'] = video_index
                progress_data['total_videos'] = total_videos
            
            download_progress[task_id] = progress_data
            logger.info(f"Task {task_id} progress: {overall_percentage:.1f}% - Speed: {d.get('speed', 0)/1024/1024:.2f} MB/s - ETA: {d.get('eta', 0)}s")
            
    elif d['status'] == 'finished':
        logger.info(f"Task {task_id}: Download finished, starting conversion")
        if video_index is not None and total_videos is not None:
            overall_percentage = (video_index / total_videos) * 100
        else:
            overall_percentage = 95
            
        progress_data = {
            'status': 'converting',
            'percentage': round(overall_percentage, 1),
            'message': 'Converting to MP3...'
        }
        
        if video_index is not None:
            progress_data['current_video'] = video_index
            progress_data['total_videos'] = total_videos
            
        download_progress[task_id] = progress_data
        logger.info(f"Task {task_id}: Download finished, converting to MP3 (video {video_index or 'single'})")

@app.get("/")
async def read_root():
    """Serve the main page"""
    logger.info("GET / - Serving main page")
    return FileResponse("static/index.html")

@app.post("/api/video-info")
async def get_video_info(request: DownloadRequest):
    """Get video/playlist information without downloading"""
    logger.info(f"POST /api/video-info - URL: {request.url}")
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': 'in_playlist',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.debug(f"Extracting info from: {request.url}")
            info = ydl.extract_info(str(request.url), download=False)
            
        # Check if it's a playlist
        is_playlist = 'entries' in info
        logger.info(f"URL is {'playlist' if is_playlist else 'single video'}")

        if is_playlist:
            entries = list(info['entries'])
            videos = []
            
            for entry in entries[:50]:  # Limit to first 50 for display
                if entry:
                    videos.append({
                        'title': entry.get('title', 'Unknown'),
                        'duration': entry.get('duration', 0),
                        'url': entry.get('url', ''),
                    })
            
            logger.info(f"Playlist info retrieved: {info.get('title', 'Unknown')} with {len(entries)} videos")
            
            return {
                'success': True,
                'is_playlist': True,
                'info': {
                    'title': info.get('title', 'Unknown Playlist'),
                    'uploader': info.get('uploader', 'Unknown'),
                    'video_count': len(entries),
                    'videos': videos
                }
            }
        else:
            # Single video
            logger.info(f"Video info retrieved: {info.get('title', 'Unknown')} by {info.get('uploader', 'Unknown')}")
            
            return {
                'success': True,
                'is_playlist': False,
                'info': {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0)
                }
            }
    except Exception as e:
        logger.error(f"Error getting video info for {request.url}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download")
async def download_video(request: DownloadRequest):
    """Download and convert video(s) to MP3"""
    task_id = str(uuid.uuid4())
    logger.info(f"POST /api/download - Task {task_id} started for URL: {request.url}")
    
    try:
        # Initialize progress
        download_progress[task_id] = {
            'status': 'starting',
            'percentage': 0
        }
        
        # First check if it's a playlist
        ydl_opts_check = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': 'in_playlist',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_check) as ydl:
            logger.debug(f"Checking URL type for: {request.url}")
            info = ydl.extract_info(str(request.url), download=False)
            is_playlist = 'entries' in info
        
        logger.info(f"Task {task_id} - URL type: {'playlist' if is_playlist else 'single video'}")

        if is_playlist:
            # Playlist download - NEW APPROACH
            async def download_playlist_task():
                try:
                    entries = list(info['entries'])
                    total_videos = len(entries)
                    downloaded_files = []
                    
                    logger.info(f"Task {task_id} - Starting playlist download with {total_videos} videos")
                    
                    download_progress[task_id] = {
                        'status': 'downloading',
                        'percentage': 0,
                        'total_videos': total_videos,
                        'current_video': 0,
                        'is_playlist': True
                    }
                    
                    # Create task directory
                    task_dir = os.path.join(DOWNLOADS_DIR, task_id)
                    os.makedirs(task_dir, exist_ok=True)
                    logger.debug(f"Task {task_id} - Created directory: {task_dir}")
                    
                    for idx, entry in enumerate(entries):
                        if not entry:
                            logger.warning(f"Task {task_id} - Skipping empty entry at index {idx}")
                            continue
                        
                        current_video_num = idx + 1
                        video_url = entry['url']
                        logger.info(f"Task {task_id} - Processing video {current_video_num}/{total_videos}: {video_url}")
                        
                        # Get video info first to get the title
                        try:
                            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl_info:
                                video_info = ydl_info.extract_info(video_url, download=False)
                                original_title = video_info.get('title', f'video_{current_video_num}')
                                safe_title = sanitize_filename(original_title)
                                logger.info(f"Task {task_id} - Video title: {original_title}")
                        except Exception as e:
                            logger.warning(f"Task {task_id} - Could not get video title: {e}")
                            safe_title = f"video_{current_video_num}"
                        
                        # Download with proper filename
                        ydl_opts = {
                            'format': 'bestaudio/best',
                            'postprocessors': [{
                                'key': 'FFmpegExtractAudio',
                                'preferredcodec': 'mp3',
                                'preferredquality': '192',
                            }],
                            'outtmpl': os.path.join(task_dir, f'{safe_title}.%(ext)s'),
                            'quiet': False,
                            'no_warnings': False,
                            'progress_hooks': [lambda d, idx=current_video_num, total=total_videos: progress_hook(d, task_id, idx, total)],
                        }
                        
                        try:
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                logger.info(f"Task {task_id} - Downloading video {current_video_num}: {original_title}")
                                ydl.extract_info(video_url, download=True)
                                
                            # Find the actual downloaded file
                            expected_filename = f"{safe_title}.mp3"
                            expected_path = os.path.join(task_dir, expected_filename)
                            
                            if os.path.exists(expected_path):
                                downloaded_files.append({
                                    'filename': expected_filename,
                                    'title': original_title,
                                    'path': expected_path
                                })
                                logger.info(f"Task {task_id} - Successfully downloaded: {original_title}")
                            else:
                                # Try to find any .mp3 file in the directory
                                mp3_files = [f for f in os.listdir(task_dir) if f.endswith('.mp3')]
                                if mp3_files:
                                    actual_filename = mp3_files[-1]  # Get the most recent
                                    actual_path = os.path.join(task_dir, actual_filename)
                                    # Rename to proper title
                                    new_filename = f"{safe_title}.mp3"
                                    new_path = os.path.join(task_dir, new_filename)
                                    os.rename(actual_path, new_path)
                                    downloaded_files.append({
                                        'filename': new_filename,
                                        'title': original_title,
                                        'path': new_path
                                    })
                                    logger.info(f"Task {task_id} - Renamed {actual_filename} to {new_filename}")
                        
                        except Exception as e:
                            logger.error(f"Task {task_id} - Failed to download video {current_video_num}: {str(e)}")
                            continue
                        
                        # Update progress after each video
                        progress_percentage = (current_video_num / total_videos) * 100
                        download_progress[task_id] = {
                            'status': 'downloading',
                            'percentage': round(progress_percentage, 1),
                            'total_videos': total_videos,
                            'current_video': current_video_num,
                            'is_playlist': True,
                            'current_title': original_title
                        }
                    
                    logger.info(f"Task {task_id} - All videos downloaded. Creating ZIP file with {len(downloaded_files)} files")
                    
                    # Create ZIP file with proper names
                    zip_filename = f"{sanitize_filename(info.get('title', 'playlist'))}.zip"
                    zip_path = os.path.join(DOWNLOADS_DIR, zip_filename)
                    
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for file_info in downloaded_files:
                            if os.path.exists(file_info['path']):
                                # Use the proper title as the filename in ZIP
                                zip_filename_in_archive = f"{file_info['title']}.mp3"
                                zipf.write(file_info['path'], zip_filename_in_archive)
                                logger.debug(f"Task {task_id} - Added to ZIP: {zip_filename_in_archive}")
                            else:
                                logger.warning(f"Task {task_id} - File not found for ZIP: {file_info['path']}")
                    
                    logger.info(f"Task {task_id} - ZIP file created successfully: {zip_filename}")
                    
                    # Clean up individual files
                    try:
                        import shutil
                        shutil.rmtree(task_dir)
                        logger.debug(f"Task {task_id} - Cleaned up temporary directory")
                    except Exception as e:
                        logger.warning(f"Task {task_id} - Could not clean up temporary directory: {e}")
                    
                    download_progress[task_id] = {
                        'status': 'completed',
                        'percentage': 100,
                        'filename': zip_filename,
                        'title': info.get('title', 'Playlist'),
                        'total_videos': total_videos,
                        'is_playlist': True
                    }
                    
                    logger.info(f"Task {task_id} - Playlist download completed successfully")
                    
                except Exception as e:
                    logger.error(f"Task {task_id} - Playlist download failed: {str(e)}", exc_info=True)
                    download_progress[task_id] = {
                        'status': 'error',
                        'message': str(e)
                    }
            
            asyncio.create_task(download_playlist_task())
            
        else:
            # Single video download
            async def download_single_task():
                try:
                    logger.info(f"Task {task_id} - Starting single video download from: {request.url}")
                    
                    # Get video info first to get proper title
                    with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl_info:
                        video_info = ydl_info.extract_info(str(request.url), download=False)
                        original_title = video_info.get('title', 'Unknown')
                        safe_title = sanitize_filename(original_title)
                        logger.info(f"Task {task_id} - Video title: {original_title}")
                    
                    ydl_opts = {
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
                        'outtmpl': os.path.join(DOWNLOADS_DIR, f'{task_id}.%(ext)s'),  # Temporary name
                        'quiet': False,
                        'no_warnings': False,
                        'progress_hooks': [lambda d: progress_hook(d, task_id)],
                    }
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        logger.debug(f"Task {task_id} - Extracting and downloading video")
                        ydl.extract_info(str(request.url), download=True)
                    
                    # Rename the file from task_id to proper title
                    temp_filename = f"{task_id}.mp3"
                    temp_path = os.path.join(DOWNLOADS_DIR, temp_filename)
                    final_filename = f"{safe_title}.mp3"
                    final_path = os.path.join(DOWNLOADS_DIR, final_filename)
                    
                    if os.path.exists(temp_path):
                        os.rename(temp_path, final_path)
                        logger.info(f"Task {task_id} - Renamed {temp_filename} to {final_filename}")
                    else:
                        # If the expected file doesn't exist, try to find any .mp3 file
                        mp3_files = [f for f in os.listdir(DOWNLOADS_DIR) if f.endswith('.mp3') and task_id in f]
                        if mp3_files:
                            actual_temp_filename = mp3_files[0]
                            actual_temp_path = os.path.join(DOWNLOADS_DIR, actual_temp_filename)
                            os.rename(actual_temp_path, final_path)
                            logger.info(f"Task {task_id} - Renamed {actual_temp_filename} to {final_filename}")
                        else:
                            final_filename = temp_filename  # Fallback to original name
                            logger.warning(f"Task {task_id} - Could not find downloaded file to rename")
                    
                    download_progress[task_id] = {
                        'status': 'completed',
                        'percentage': 100,
                        'filename': final_filename,
                        'title': original_title,
                        'is_playlist': False
                    }
                    
                    logger.info(f"Task {task_id} - Single video download completed successfully: {original_title}")
                    
                except Exception as e:
                    logger.error(f"Task {task_id} - Single video download failed: {str(e)}", exc_info=True)
                    download_progress[task_id] = {
                        'status': 'error',
                        'message': str(e)
                    }
            
            asyncio.create_task(download_single_task())
        
        logger.info(f"Task {task_id} - Download task created successfully")
        
        return {
            'success': True,
            'task_id': task_id,
            'is_playlist': is_playlist
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} - Failed to create download task: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """Get download progress"""
    logger.debug(f"GET /api/progress/{task_id} - Checking progress")
    
    if task_id not in download_progress:
        logger.warning(f"Progress check failed - Task not found: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found")
    
    progress = download_progress[task_id]
    logger.debug(f"Task {task_id} progress: {progress['status']} - {progress.get('percentage', 0)}%")
    
    return progress

@app.get("/api/download-file/{filename}")
async def download_file(filename: str):
    """Download the completed MP3 file or ZIP"""
    logger.info(f"GET /api/download-file/{filename} - File download requested")
    
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type and set proper filename for download
    if filename.endswith('.zip'):
        media_type = "application/zip"
        # Use the original filename which now contains the proper title
        download_filename = filename
        logger.debug(f"Serving ZIP file: {filename}")
    else:
        media_type = "audio/mpeg"
        # For single files, the filename already contains the proper title
        download_filename = filename
        logger.debug(f"Serving MP3 file: {filename}")
    
    file_size = os.path.getsize(file_path)
    logger.info(f"File served successfully: {filename} ({file_size} bytes)")
    
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=download_filename  # This will be the proper title
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Additional endpoint to view recent logs
@app.get("/api/logs")
async def get_recent_logs(lines: int = 100):
    """Get recent application logs (for debugging)"""
    try:
        with open('app.log', 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        return {
            "success": True,
            "lines": lines,
            "logs": recent_lines
        }
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 YouTube MP3 Downloader API starting up...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 YouTube MP3 Downloader API shutting down...")