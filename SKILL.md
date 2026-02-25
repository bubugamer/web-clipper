---
name: web-clipper
description: Save, categorize, and archive web content locally. Use when the user wants to bookmark/clip/save/收藏 a webpage, article, blog post, podcast, or video. Handles text extraction to markdown, image downloading, video downloading (via yt-dlp), and podcast audio downloading. Stores metadata (URL, author, date, size, tags) for all clips.
---

# Web Clipper

Save web content to `~/.openclaw/workspace/clips/` with full metadata.

## Directory Structure

```
clips/
├── index.json              # 全局索引 + known_tags
├── _INDEX.md               # Obsidian MOC (auto-generated)
├── _TAGS.md                # Obsidian 标签聚合 (auto-generated)
├── articles/               # 文章（可含子目录）
│   ├── NodeSeek/
│   └── 微信公众号-xxx/
└── Media/
    ├── Audio/  ├── Games/  ├── pics/  └── videos/
```

## Commands

```bash
CLIP=~/.npm-global/lib/node_modules/openclaw/skills/web-clipper/scripts

# Clip article (auto Cloudflare bypass + screenshot + HTML→Markdown)
python3 $CLIP/clip.py clip "URL" --type article --title "标题" --tags tech ai --author "作者"
python3 $CLIP/clip.py clip "URL" --type article --source "NodeSeek" --title "标题"
python3 $CLIP/clip.py clip "URL" --type article --subcategory "VPS" --title "标题"

# Clip video / audio
python3 $CLIP/clip.py clip "URL" --type video --title "标题"
python3 $CLIP/clip.py clip "URL" --type audio --title "播客标题"

# Transcribe / List / Tags / Subcategories
python3 $CLIP/clip.py transcribe "Media/Audio/2026-02-24-episode"
python3 $CLIP/clip.py list --type article --tag tech --limit 10
python3 $CLIP/clip.py tags
python3 $CLIP/clip.py subcategories --base articles
```

## Agent Workflow

### 1. Type & Category
- Article → `articles/` | Video → `Media/videos/` | Audio → `Media/Audio/` | Image → `Media/pics/`

### 2. Sub-categorization (articles)
- `--source "NodeSeek"` or `--subcategory "VPS"`
- ⚠️ **ASK user before creating new subfolders**

### 3. Tags — run `tags` first, reuse existing, add new freely

### 4. Fetch (automatic escalation in clip.py)
1. **curl** → 2. **Stealth browser** (Xvfb + undetected-chromedriver, auto on Cloudflare) → 3. Save `fetch_failed` + report

### 5. Post-clip (articles) — automatic in clip.py
1. Full-page screenshot → `screenshot.png` (visual backup)
2. HTML → markdownify → `content.md` (preserves headings, code blocks, lists, images, quotes)
3. Download images → `images/` with local path replacement
4. YAML frontmatter (title, url, author, tags, source)
5. Auto-generate `_INDEX.md` + `_TAGS.md` for Obsidian
6. Auto git commit + push to GitHub (Obsidian sync)

### 6. Transcription — `whisper small` model, Chinese default

## Environment

- Python venv: `~/.openclaw/workspace/.venv/` (whisper, undetected-chromedriver, markdownify)
- Chromium: `~/.cache/ms-playwright/chromium-1208/`
- Tools: `curl`, `yt-dlp`, `ffmpeg`, `Xvfb`, `agent-browser`
