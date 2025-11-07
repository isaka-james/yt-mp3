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
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
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

def get_video_info_safe(url):
    """Extract video info safely"""
    try:
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        logger.warning(f"Could not get video info for {url}: {e}")
        return None

def progress_hook(d, task_id, video_index=None, total_videos=None):
    """Hook to track download progress"""
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        
        if total > 0:
            percentage = (downloaded / total) * 100
            
            # Calculate overall progress for playlists
            if video_index is not None and total_videos is not None:
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

    elif d['status'] == 'finished':
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

async def download_single_video(task_id, url):
    """Download and convert a single video to MP3"""
    try:
        logger.info(f"Task {task_id} - Starting single video download")
        
        # Get video info for proper naming
        video_info = get_video_info_safe(url)
        if not video_info:
            raise Exception("Could not retrieve video information")
            
        video_title = video_info.get('title', 'Unknown')
        safe_title = sanitize_filename(video_title)
        final_filename = f"{safe_title}.mp3"
        final_path = os.path.join(DOWNLOADS_DIR, final_filename)
        
        # Skip if file already exists
        if os.path.exists(final_path):
            logger.info(f"Task {task_id} - File already exists: {final_filename}")
            download_progress[task_id] = {
                'status': 'completed',
                'percentage': 100,
                'filename': final_filename,
                'title': video_title,
                'is_playlist': False
            }
            return

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(DOWNLOADS_DIR, f'{safe_title}.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [lambda d: progress_hook(d, task_id)],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.extract_info, url, download=True)

        # Verify file was created
        if not os.path.exists(final_path):
            # Look for any .mp3 file with the safe title
            pattern = re.compile(re.escape(safe_title) + r'.*\.mp3$')
            for filename in os.listdir(DOWNLOADS_DIR):
                if pattern.match(filename):
                    final_filename = filename
                    final_path = os.path.join(DOWNLOADS_DIR, filename)
                    break
            else:
                raise FileNotFoundError(f"Downloaded file not found for {safe_title}")

        download_progress[task_id] = {
            'status': 'completed',
            'percentage': 100,
            'filename': final_filename,
            'title': video_title,
            'is_playlist': False
        }

        logger.info(f"Task {task_id} - Single video download completed: {video_title}")

    except Exception as e:
        logger.error(f"Task {task_id} - Single video download failed: {str(e)}", exc_info=True)
        download_progress[task_id] = {
            'status': 'error',
            'message': str(e)
        }

async def download_playlist(task_id, url, playlist_info):
    """Download and convert a playlist to MP3 files in a ZIP"""
    try:
        entries = list(playlist_info['entries'])
        total_videos = len(entries)
        downloaded_files = []

        logger.info(f"Task {task_id} - Starting playlist download with {total_videos} videos")

        # Create task directory
        task_dir = os.path.join(DOWNLOADS_DIR, task_id)
        os.makedirs(task_dir, exist_ok=True)

        download_progress[task_id] = {
            'status': 'downloading',
            'percentage': 0,
            'total_videos': total_videos,
            'current_video': 0,
            'is_playlist': True
        }

        for idx, entry in enumerate(entries):
            if not entry:
                continue

            current_video_num = idx + 1
            video_url = entry['url']
            
            # Get video info for proper naming
            video_info = get_video_info_safe(video_url)
            if not video_info:
                logger.warning(f"Task {task_id} - Could not get info for video {current_video_num}, skipping")
                continue
                
            video_title = video_info.get('title', f'Video_{current_video_num}')
            safe_title = sanitize_filename(video_title)
            
            # Create unique filename for each video in playlist
            unique_safe_title = f"{safe_title}_{current_video_num:03d}"
            expected_filename = f"{unique_safe_title}.mp3"
            expected_path = os.path.join(task_dir, expected_filename)

            logger.info(f"Task {task_id} - Processing video {current_video_num}/{total_videos}: {video_title}")

            # Skip if file already exists in this session
            if not os.path.exists(expected_path):
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': os.path.join(task_dir, f'{unique_safe_title}.%(ext)s'),  # Use unique filename
                    'quiet': False,
                    'no_warnings': False,
                    'progress_hooks': [lambda d, idx=current_video_num, total=total_videos: progress_hook(d, task_id, idx, total)],
                }

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        await asyncio.to_thread(ydl.extract_info, video_url, download=True)
                except Exception as e:
                    logger.error(f"Task {task_id} - Failed to download video {current_video_num}: {str(e)}")
                    continue

            # Verify file was created
            if os.path.exists(expected_path):
                downloaded_files.append({
                    'filename': expected_filename,
                    'title': video_title,
                    'path': expected_path
                })
            else:
                # Try to find the actual downloaded file with unique pattern
                pattern = re.compile(re.escape(unique_safe_title) + r'.*\.mp3$')
                for filename in os.listdir(task_dir):
                    if pattern.match(filename):
                        actual_path = os.path.join(task_dir, filename)
                        downloaded_files.append({
                            'filename': filename,
                            'title': video_title,
                            'path': actual_path
                        })
                        break
                else:
                    logger.warning(f"Task {task_id} - Could not find downloaded file for: {video_title}")

            # Update progress
            progress_percentage = (current_video_num / total_videos) * 100
            download_progress[task_id] = {
                'status': 'downloading',
                'percentage': round(progress_percentage, 1),
                'total_videos': total_videos,
                'current_video': current_video_num,
                'is_playlist': True,
                'current_title': video_title
            }

        # Create ZIP file
        if downloaded_files:
            playlist_title = sanitize_filename(playlist_info.get('title', 'playlist'))
            zip_filename = f"{playlist_title}_{task_id}.zip"
            zip_path = os.path.join(DOWNLOADS_DIR, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in downloaded_files:
                    if os.path.exists(file_info['path']):
                        # Use original title for filename in ZIP (without the unique suffix)
                        zip_filename_in_archive = f"{file_info['title']}.mp3"
                        zipf.write(file_info['path'], zip_filename_in_archive)
                        logger.debug(f"Task {task_id} - Added to ZIP: {zip_filename_in_archive}")

            # Clean up temporary files
            import shutil
            shutil.rmtree(task_dir)
            logger.debug(f"Task {task_id} - Cleaned up temporary directory: {task_dir}")

            download_progress[task_id] = {
                'status': 'completed',
                'percentage': 100,
                'filename': zip_filename,
                'title': playlist_info.get('title', 'Playlist'),
                'total_videos': total_videos,
                'is_playlist': True,
                'message': f'Download completed. Files saved on server as: {zip_filename}'
            }

            logger.info(f"Task {task_id} - Playlist download completed: {zip_filename} with {len(downloaded_files)} files")
        else:
            raise Exception("No videos were successfully downloaded")

    except Exception as e:
        logger.error(f"Task {task_id} - Playlist download failed: {str(e)}", exc_info=True)
        # Clean up on error
        try:
            task_dir = os.path.join(DOWNLOADS_DIR, task_id)
            if os.path.exists(task_dir):
                import shutil
                shutil.rmtree(task_dir)
        except Exception as cleanup_error:
            logger.warning(f"Task {task_id} - Cleanup failed: {cleanup_error}")
            
        download_progress[task_id] = {
            'status': 'error',
            'message': str(e)
        }

@app.get("/")
async def read_root():
    """Serve the main page"""
    return FileResponse("static/index.html")

@app.post("/api/video-info")
async def get_video_info(request: DownloadRequest):
    """Get video/playlist information without downloading"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(str(request.url), download=False)

        is_playlist = 'entries' in info

        if is_playlist:
            entries = list(info['entries'])
            videos = []

            for entry in entries[:50]:  # Limit to first 50
                if entry:
                    videos.append({
                        'title': entry.get('title', 'Unknown'),
                        'duration': entry.get('duration', 0),
                        'url': entry.get('url', ''),
                    })

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
    """Download and convert video(s) to MP3 - Files saved on server only"""
    task_id = str(uuid.uuid4())
    
    try:
        # Initialize progress
        download_progress[task_id] = {
            'status': 'starting',
            'percentage': 0,
            'message': 'Initializing download...'
        }

        # Check if it's a playlist
        ydl_opts_check = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts_check) as ydl:
            info = ydl.extract_info(str(request.url), download=False)
            is_playlist = 'entries' in info

        if is_playlist:
            # Start playlist download
            asyncio.create_task(download_playlist(task_id, str(request.url), info))
        else:
            # Start single video download
            asyncio.create_task(download_single_video(task_id, str(request.url)))

        return {
            'success': True,
            'task_id': task_id,
            'is_playlist': is_playlist,
            'message': 'Download started. Files will be saved on server.'
        }

    except Exception as e:
        logger.error(f"Task {task_id} - Failed to create download task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """Get download progress"""
    if task_id not in download_progress:
        raise HTTPException(status_code=404, detail="Task not found")

    return download_progress[task_id]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/logs")
async def get_recent_logs(lines: int = 100):
    """Get recent application logs"""
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