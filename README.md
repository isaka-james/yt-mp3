# 🎧 YT-MP3 Tool - For When You Want Music Without the Streaming Drama

Linux gang, this one's for you. Tired of `yay -S` installing 50 dependencies just to download a playlist? This tool gets straight to the point.

## 🤔 What Even Is This?

### The Two Scripts Explained:

**`mix.py`** - For when YouTube's algorithm hits different
- Downloads YouTube Mixes & Radio stations  
- Like when you're listening to a song and YouTube goes "here's more stuff you'll probably vibe with"
- Perfect for discovering new music without commitment
- [What's a YouTube Mix?](https://www.google.com/search?q=what+is+youtube+mix)

**`playlist.py`** - For your actual curated playlists
- Downloads proper playlists (your Liked Songs, created playlists, etc.)
- Uses parallel downloads because we're not in the Stone Age
- Organizes everything properly like the organized king/queen you are
- [Playlists vs Mixes](https://www.google.com/search?q=youtube+mix+vs+playlist)

## 🎵 Supports Both YouTube & YouTube Music

**This tool works with BOTH:**
- `youtube.com` URLs (the regular YouTube we all know and love)
- `music.youtube.com` URLs (YouTube Music, for the cultured folks)

So whether you're grabbing from regular YouTube or YouTube Music - it just works. No separate tools needed.

## 🚀 Installation (The Linux Way)

```bash
# You probably have Python, but just in case
sudo pacman -S python python-pip  # Arch gang
# or
sudo apt install python3 python3-pip  # Debian/Ubuntu crew

# The only dependency that matters
pip install yt-dlp

# Clone this bad boy
git clone https://github.com/isaka-james/yt-mp3
cd yt-mp3

# Make them executable (because we're fancy)
chmod +x mix.py playlist.py
```

## 🎯 Usage Examples That Actually Work

### For Algorithm-Generated Mixes (Both Platforms):
```bash
# YouTube Music Mix
./mix.py "https://music.youtube.com/watch?v=9XV2XGyn25k&list=RDAMVM9XV2XGyn25k" 25

# Regular YouTube Mix  
./mix.py "https://www.youtube.com/watch?v=SxAp27sFaIM&list=RDSxAp27sFaIM" 25
```

### For Your Actual Playlists (Both Platforms):
```bash
# YouTube Music Playlist
./playlist.py "https://music.youtube.com/playlist?list=PLv1HTPB7i3ZZ9navMdw0GH1cpNY3gFB3N"

# Regular YouTube Playlist
./playlist.py "https://www.youtube.com/playlist?list=PLxyz123456789"
```

## 📁 Where Your Files Actually Go

```
downloads/
├── "Chill Coding Mix"/          # Each mix/playlist gets its own folder
│   ├── song1.mp3
│   ├── song2.mp3
│   └── ...
└── "My Liked Songs"/
    ├── that_banger.mp3
    ├── another_banger.mp3
    └── ...
```

**Pro tip:** `cd downloads && ls -la` to see your loot. Or use `ranger` if you're extra.

## 🧠 What's Actually Happening Under the Hood

- **`mix.py`**: Downloads sequentially (one song at a time) because mixes are for vibing, not rushing
- **`playlist.py`**: Uses 3 parallel threads because your time is valuable  
- **Both work with YouTube AND YouTube Music** - no separate tools needed
- Automatically sanitizes filenames (no more `[Official Music Video].mp3` nonsense)
- All files are proper MP3s ready for your music player of choice

## 🐛 Common Issues & Fixes

### "Command not found"
```bash
python3 mix.py "your_url" 25  # Use python3 explicitly
```

### "ModuleNotFoundError: No module named 'yt_dlp'"
```bash
pip install --user yt-dlp  # Sometimes pip needs the --user flag
```

### "This URL is not working"
- Make sure it's from `music.youtube.com` or `youtube.com` (both work!)
- Check if the playlist is public  
- Try copying the "Share" link instead of the address bar URL

### "Downloads are slow af"
- `playlist.py` already uses parallel downloads
- For mixes, that's just how YouTube serves them ¯\\_(ツ)_/¯
- Use `--max-workers 5` in the code if you want to get wild

## 🚀 Pro Tips for Power Users

```bash
# Add to your .bashrc for quick access
alias yt-mix="python3 /path/to/mix.py"
alias yt-playlist="python3 /path/to/playlist.py"

# Now you can just do:
yt-mix "your_url" 20
yt-playlist "your_playlist_url"
```

**Want to customize?** The code is right there. Change `max_workers`, output directories, whatever. It's your party.

## ⚖️ Legal Stuff (The Boring Part)

- This is for personal use only
- Don't be a dick and mass download copyrighted content  
- Support artists when you can (streaming revenue still matters)
- If you're a record label, please don't sue me I'm broke

## 🎉 Why This Over Other Tools?

- **No bloat**: 2 files, 1 dependency
- **Actually works with both YouTube AND YouTube Music** - one tool to rule them all
- **Proper file organization** (not just dumping everything in ~/Downloads)
- **Parallel downloads** that don't nuke your CPU
- **Written for Linux** by someone who actually uses Linux

---

## 🪟 BTW Windows Users Can Use This Too

Yeah yeah, we see you over there. You can join the party too:

1. **Install Python** from [python.org](https://python.org)
2. **Open Command Prompt** (yes, that black box you're scared of)  
3. **Run these commands**:
```cmd
pip install yt-dlp
python mix.py "your_youtube_url" 25
```

Same scripts, same vibe. Works with both YouTube and YouTube Music. No excuses.

---

**Made for the terminal warriors who just want their music without 15 layers of abstraction**

*If this saved you from yet another Electron app, hit that star button ⭐*

**Contributions welcome** - especially if you make the error messages even more sassy