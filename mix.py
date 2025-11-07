#!/usr/bin/env python3
"""
Simple YouTube Mix Downloader
"""

import yt_dlp
import os
import sys

def download_mix_simple(mix_url, limit=25):
    """Simple approach - let yt-dlp handle everything"""
    output_template = 'downloads/%(playlist_title)s/%(title)s.%(ext)s'
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
        'playlistend': limit,  # Limit number of videos
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([mix_url])
        print("Mix download completed!")
    except Exception as e:
        print(f"Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_mix.py <youtube_mix_url> [limit]")
        sys.exit(1)
    
    mix_url = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 25
    
    download_mix_simple(mix_url, limit)

if __name__ == "__main__":
    main()
