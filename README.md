# 🎧 YT-MP3 Tool - Download Playlists Without The Drama

When you find that fire playlist but it's stuck on YouTube 😤 This tool gets your music offline, no cap.

<details>
<summary>🤔 <b>What even is this?</b> (click me)</summary>

### Two scripts, zero headaches:

**`mix.py`** - For when YouTube's algorithm actually slaps
- Downloads YouTube Mixes & Radio stations  
- That "My Mix" that somehow knows your vibe better than you
- Perfect for when you're in your feels or need new music

**`playlist.py`** - For your actual curated playlists  
- Your Liked Songs, created playlists, the works
- Downloads multiple songs at once because we're not in 2010
- Organizes everything so you don't have 100 files called "audio.mp3"

**Works with BOTH:**
- `youtube.com` (the OG)
- `music.youtube.com` (for the cultured folks)

One tool to rule them all 💍
</details>

## 🚀 Quick Start (Just Give Me The Commands)

```bash
# Our Magic Dependency (We can't write YT integration from scratch!)
pip install yt-dlp

# For mixes (algorithm-generated playlists)
python3 mix.py "your_youtube_mix_url" 25

# For actual playlists (your Liked Songs, etc.)
python3 playlist.py "your_playlist_url"
```

<details>
<summary>📁 <b>Where my files go?</b></summary>

```
downloads/
├── "Vibe Check Mix"/
│   ├── song_that_slaps.mp3
│   └── another_banger.mp3
└── "My Liked Songs"/
    ├── that_one_song.mp3
    └── you_get_the_idea.mp3
```

Each playlist gets its own folder. Your files won't be a hot mess 🔥
</details>

<details>
<summary>🛠️ <b>Installation</b> (if you don't have it yet)</summary>

### Normal Linux:
```bash
pip install yt-dlp
```

### Kali/Protected Systems (when pip yells at you):
```bash
# Python venv to the rescue:
python3 -m venv ~/yt-mp3-env
source ~/yt-mp3-env/bin/activate
pip install yt-dlp

# Pro tip: Add to ~/.bashrc
alias yt-env="source ~/yt-mp3-env/bin/activate"
```

### Get the scripts:
```bash
git clone https://github.com/isaka-james/yt-mp3
cd yt-mp3
chmod +x mix.py playlist.py
```
</details>

<details>
<summary>🎯 <b>Real Examples That Actually Work</b></summary>

### Mixes (YouTube Radio):
```bash
python3 mix.py "https://music.youtube.com/watch?v=9XV2XGyn25k&list=RDAMVM9XV2XGyn25k" 25
python3 mix.py "https://www.youtube.com/watch?v=SxAp27sFaIM&list=RDSxAp27sFaIM" 30
```

### Actual Playlists:
```bash
python3 playlist.py "https://music.youtube.com/playlist?list=PLv1HTPB7i3ZZ9navMdw0GH1cpNY3gFB3N"
python3 playlist.py "https://www.youtube.com/playlist?list=PLxyz123456789"
```

**Pro tip:** Use the "Share" link from YouTube/YouTube Music for best results
</details>

<details>
<summary>🐛 <b>Common Issues & Fixes</b></summary>

### "externally-managed-environment" (Kali users):
```bash
python3 -m venv ~/yt-mp3-env
source ~/yt-mp3-env/bin/activate
pip install yt-dlp
```

### "Command not found":
```bash
python3 mix.py "url" 25  # Use python3 not python
```

### "Module not found":
- Kali users: Make sure venv is activated
- Others: `pip install --user yt-dlp`

### "URL not working":
- Make sure it's from youtube.com or music.youtube.com
- Try the "Share" link instead of address bar
- Check if playlist is public
</details>

<details>
<summary>🚀 <b>Pro Tips</b> (for the power users)</summary>

```bash
# Add to your .bashrc for instant access
alias yt-mix="python3 /path/to/mix.py"
alias yt-playlist="python3 /path/to/playlist.py"

# Kali users add this too:
alias yt-env="source ~/yt-mp3-env/bin/activate"

# Now just do:
yt-mix "url" 20        # Normal Linux
yt-env && yt-mix "url" # Kali
```

**Customization?** The code is right there. Change threads, folders, whatever. It's your party 🎉
</details>

<details>
<summary>🪟 <b>Windows Users Can Join Too</b></summary>

Yeah we see you:

1. **Install Python** from [python.org](https://python.org)
2. **Open Command Prompt** (that scary black box)
3. **Run:**
```cmd
pip install yt-dlp
python mix.py "your_url" 25
```

Same scripts, same vibe. No excuses.
</details>

---

**Made for when you just want your music without 15 layers of abstraction**

*If this saved you from subscription hell, hit that star ⭐*

**PS:** Don't mass download copyrighted stuff. Support artists when you can 🎵