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
├── articles/               # 文章（可含子目录：按来源或主题）
│   ├── NodeSeek/           # 按来源分
│   ├── 微信公众号-xxx/      # 按公众号分
│   └── VPS/                # 按主题分
└── Media/
    ├── Audio/              # 播客、音乐
    ├── Games/              # 游戏相关
    ├── pics/               # 图片
    └── videos/             # 视频
```

## Commands

```bash
CLIP=~/.npm-global/lib/node_modules/openclaw/skills/web-clipper/scripts

# Clip article (自动处理 Cloudflare)
python3 $CLIP/clip.py clip "URL" --type article --title "标题" --tags tech ai --author "作者"

# Clip article with source subfolder
python3 $CLIP/clip.py clip "URL" --type article --source "微信公众号-xxx" --title "标题"

# Clip article with topic subfolder
python3 $CLIP/clip.py clip "URL" --type article --subcategory "VPS" --title "标题"

# Clip video / audio
python3 $CLIP/clip.py clip "URL" --type video --title "标题"
python3 $CLIP/clip.py clip "URL" --type audio --title "播客标题"

# Transcribe audio (whisper)
python3 $CLIP/clip.py transcribe "Media/Audio/2026-02-24-episode"

# List clips / tags / subcategories
python3 $CLIP/clip.py list --type article --tag tech --limit 10
python3 $CLIP/clip.py tags
python3 $CLIP/clip.py subcategories --base articles
```

## Agent Workflow

### 1. Determine type & category
- Article → `articles/` (with optional source or subcategory subfolder)
- Video → `Media/videos/`
- Podcast/Audio → `Media/Audio/`
- Image → `Media/pics/`

### 2. Sub-categorization (articles only)
- By source: `--source "微信公众号-xxx"` → `articles/微信公众号-xxx/`
- By topic: `--subcategory "VPS"` → `articles/VPS/`
- ⚠️ **Before creating any new subfolder**, run `subcategories` to check existing ones, then **ASK the user** for confirmation. Only create after approval.

### 3. Tags
- Run `tags` command first to see existing tags for reuse
- Assign tags based on content understanding; prefer reusing existing tags
- Add new tags freely when no existing tag fits

### 4. Fetching strategy (automatic escalation in clip.py)
clip.py handles the escalation chain automatically for articles:

1. **curl** (default, fast)
2. **Stealth browser** (auto-triggered when Cloudflare detected):
   - Xvfb virtual display + undetected-chromedriver (non-headless)
   - Bypasses Cloudflare Turnstile, hCaptcha, and most anti-bot systems
   - Requires: `~/.openclaw/workspace/.venv/` with undetected-chromedriver
3. If both fail → saves metadata with `status: fetch_failed` and `fail_reason`

For additional manual fallback (if clip.py reports fetch_failed):
- Use **agent-browser** CLI to render the page:
  ```bash
  agent-browser open "URL"
  agent-browser snapshot
  agent-browser eval "document.body.innerText"
  agent-browser close
  ```
- Use OpenClaw **browser tool** (snapshot/navigate)
- **Never silently drop a clip request** — always report failure to user

### 5. Post-clip (articles)
1. Read `raw.html`, extract main content (skip nav/footer/ads/comments)
2. Convert to clean markdown → write `content.md` with YAML frontmatter:
   ```yaml
   ---
   title: "文章标题"
   url: https://original-url.com
   author: 作者名
   clipped_at: 2026-02-24T10:30:00+08:00
   tags: [tech, ai]
   source: NodeSeek
   ---
   ```
3. Replace image URLs with local `images/` paths

### 6. Transcription (audio)
- Whisper binary: `~/.openclaw/workspace/.venv/bin/whisper`
- Run: `python3 clip.py transcribe <clip_path>`
- Uses `small` model, Chinese language by default

## WeChat Articles (微信公众号)

WeChat article URLs (`mp.weixin.qq.com`) often need special handling:
- curl usually gets a redirect or empty page
- clip.py will auto-fallback to stealth browser
- Source subfolder: `微信公众号-<公众号名称>`

## Environment

- Requires: `curl`, `yt-dlp`, `ffmpeg`, `Xvfb`
- Python venv: `~/.openclaw/workspace/.venv/` (whisper + undetected-chromedriver)
- Chromium: `/home/xiemingsi/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome`
- agent-browser: globally installed via npm
- `CLIPS_DIR` env var overrides default storage path

## Storage

See [references/storage-format.md](references/storage-format.md) for full schema.
