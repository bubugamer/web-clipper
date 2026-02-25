# Web Clipper

Save, categorize, and archive web content locally with full metadata.

## Features

- **Smart fetching** — curl first, auto-fallback to Xvfb + undetected-chromedriver for Cloudflare sites
- **HTML → Markdown** — structural conversion via markdownify (preserves headings, code blocks, quotes, lists, images)
- **Full-page screenshot** — visual backup of original layout
- **Image localization** — auto-download article images, replace remote URLs with local paths
- **Smart categorization** — articles by source/topic, media by type
- **Tag management** — reusable tag system with known_tags index
- **Obsidian sync** — auto-generate `_INDEX.md` + `_TAGS.md`, git push to GitHub
- **Audio transcription** — OpenAI Whisper integration (Chinese/English)
- **Failure handling** — always saves metadata, even when fetch fails

[中文文档](README_CN.md)

## Usage

```bash
# Clip article (auto Cloudflare bypass + screenshot + HTML→Markdown)
python3 scripts/clip.py clip "URL" --type article --title "Title" --tags tech --source "NodeSeek"

# Clip video / audio
python3 scripts/clip.py clip "URL" --type video --title "Video"
python3 scripts/clip.py clip "URL" --type audio --title "Podcast"

# Transcribe / List / Tags
python3 scripts/clip.py transcribe "Media/Audio/2026-02-24-episode"
python3 scripts/clip.py list --type article --tag tech
python3 scripts/clip.py tags
```

## Requirements

- Python 3.10+, `curl`, `yt-dlp`, `ffmpeg`, `Xvfb`
- Python packages (venv): `openai-whisper`, `undetected-chromedriver`, `markdownify`
- Chromium (via Playwright)

## License

MIT
