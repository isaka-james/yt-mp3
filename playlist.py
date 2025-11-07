#!/usr/bin/env python3
"""
YouTube Playlist to MP3 Downloader
"""

import yt_dlp
import os
import sys
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

class PlaylistDownloader:
    def __init__(self, output_dir="downloads", max_workers=3):
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.downloaded_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
        os.makedirs(output_dir, exist_ok=True)
        
    def get_playlist_info(self, playlist_url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)
            return info
    
    def download_video(self, video_data):
        video_url, video_index, total_videos, playlist_title, video_title = video_data
        
        try:
            playlist_folder = sanitize_filename(playlist_title)
            playlist_path = os.path.join(self.output_dir, playlist_folder)
            os.makedirs(playlist_path, exist_ok=True)
            
            safe_title = sanitize_filename(video_title)
            output_template = os.path.join(playlist_path, f'{safe_title}.mp3')
            
            # Download as MP3 directly without conversion
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
            }
            
            print(f"Downloading [{video_index}/{total_videos}]: {video_title}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            with self.lock:
                self.downloaded_count += 1
                print(f"Completed [{video_index}/{total_videos}]: {video_title}")
            
            return True
            
        except Exception as e:
            with self.lock:
                self.failed_count += 1
                print(f"Failed [{video_index}/{total_videos}]: {video_title}")
            return False
    
    def download_playlist(self, playlist_url):
        print("Getting playlist information...")
        
        try:
            playlist_info = self.get_playlist_info(playlist_url)
            playlist_title = playlist_info.get('title', 'Unknown Playlist')
            entries = list(playlist_info['entries'])
            total_videos = len(entries)
            
            print(f"Playlist: {playlist_title}")
            print(f"Videos: {total_videos}")
            print(f"Threads: {self.max_workers}")
            print("=" * 50)
            
            video_data_list = []
            for idx, entry in enumerate(entries):
                if entry:
                    video_data = (entry['url'], idx+1, total_videos, playlist_title, 
                                entry.get('title', f'Video_{idx+1}'))
                    video_data_list.append(video_data)
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_video = {
                    executor.submit(self.download_video, video_data): video_data 
                    for video_data in video_data_list
                }
                
                for future in as_completed(future_to_video):
                    try:
                        future.result()
                    except Exception:
                        pass
            
            total_time = time.time() - start_time
            
            print("=" * 50)
            print(f"Finished in {total_time:.1f}s")
            print(f"Success: {self.downloaded_count}/{total_videos}")
            print(f"Failed: {self.failed_count}/{total_videos}")
            print(f"Location: {os.path.join(self.output_dir, sanitize_filename(playlist_title))}")
            
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python downloader.py <playlist_url>")
        sys.exit(1)
    
    playlist_url = sys.argv[1]
    
    downloader = PlaylistDownloader(max_workers=3)
    
    try:
        downloader.download_playlist(playlist_url)
    except KeyboardInterrupt:
        print("Cancelled")

if __name__ == "__main__":
    main()
