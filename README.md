# Web Clipper

Save, categorize, and archive web content locally with full metadata.

## Features

- **Article clipping** — fetch HTML, download images, convert to markdown
- **Video/Audio download** — via yt-dlp (≤1080p video, mp3 audio)
- **Cloudflare bypass** — automatic fallback using Xvfb + undetected-chromedriver
- **Whisper transcription** — transcribe audio clips to text (Chinese/English)
- **Smart categorization** — articles by source/topic, media by type
- **Tag management** — reusable tag system with known_tags index
- **Failure handling** — always saves metadata, even when fetch fails

## Directory Structure

```
clips/
├── index.json              # Global index + known_tags
├── articles/               # Articles (with optional subfolders)
│   ├── 微信公众号-xxx/      # By source
│   └── VPS/                # By topic
└── Media/
    ├── Audio/              # Podcasts, music
    ├── Games/
    ├── pics/
    └── videos/
```

## Usage

```bash
# Clip an article
python3 scripts/clip.py clip "https://example.com/article" --type article --title "Title" --tags tech

# Clip with source subfolder
python3 scripts/clip.py clip "URL" --type article --source "NodeSeek" --title "Title"

# Clip video / audio
python3 scripts/clip.py clip "URL" --type video --title "Video Title"
python3 scripts/clip.py clip "URL" --type audio --title "Podcast"

# Transcribe audio
python3 scripts/clip.py transcribe "Media/Audio/2026-02-24-episode"

# List clips / tags / subcategories
python3 scripts/clip.py list --type article --tag tech
python3 scripts/clip.py tags
python3 scripts/clip.py subcategories --base articles
```

## Fetch Strategy

Automatic escalation for articles:

1. **curl** — fast, default
2. **Stealth browser** — Xvfb + undetected-chromedriver (auto-triggered on Cloudflare)
3. **Fail gracefully** — saves metadata with `status: fetch_failed`

## Requirements

- Python 3.10+
- `curl`, `yt-dlp`, `ffmpeg`, `Xvfb`
- Python packages (in venv): `openai-whisper`, `undetected-chromedriver`
- Chromium (via Playwright or system install)

## License

MIT
