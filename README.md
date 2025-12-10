# YT-MP3: YouTube Playlist Downloader

Download YouTube and YouTube Music playlists to MP3 format.

![Tool Interface](https://github.com/user-attachments/assets/379ffe39-d2a4-4afe-b71c-3031934bd66c)

## Overview

Two specialized Python scripts for downloading YouTube content:

- **mix.py** - Downloads algorithm-generated content (YouTube Mixes, Radio stations)
- **playlist.py** - Downloads curated playlists (Liked Songs, created playlists)

Supports both `youtube.com` and `music.youtube.com` URLs.

## Requirements

```bash
pip install yt-dlp
```

## Usage

```bash
# Download YouTube Mix (specify track count)
python3 mix.py "youtube_mix_url" 25

# Download standard playlist
python3 playlist.py "playlist_url"
```

## Examples

```bash
# Mix/Radio playlist
python3 mix.py "https://music.youtube.com/watch?v=9XV2XGyn25k&list=RDAMVM9XV2XGyn25k" 25

# Standard playlist
python3 playlist.py "https://music.youtube.com/playlist?list=PLv1HTPB7i3ZZ9navMdw0GH1cpNY3gFB3N"
```

## Output Structure

```
downloads/
├── Playlist Name 1/
│   ├── track_01.mp3
│   ├── track_02.mp3
│   └── track_03.mp3
└── Playlist Name 2/
    ├── track_01.mp3
    └── track_02.mp3
```

## Installation Notes

### Standard Linux
```bash
pip install yt-dlp
```

### Systems with Protected Python (Kali, etc.)
```bash
python3 -m venv ~/yt-mp3-env
source ~/yt-mp3-env/bin/activate
pip install yt-dlp
```

## Troubleshooting

**Externally-managed-environment error:**
```bash
python3 -m venv yt-mp3-env
source yt-mp3-env/bin/activate
pip install yt-dlp
```

**Module not found:** Ensure yt-dlp is installed in active environment.

**URL issues:** Use "Share" link, verify playlist is public.

## Windows
```cmd
pip install yt-dlp
python mix.py "url" 25
```

---

*For personal use. Respect copyright and support artists.*
