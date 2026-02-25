#!/usr/bin/env python3
"""Web Clipper - Save web content locally with metadata."""

import argparse, json, os, re, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

CST = timezone(timedelta(hours=8))
CLIPS_DIR = Path(os.environ.get("CLIPS_DIR", os.path.expanduser("~/.openclaw/workspace/clips")))
INDEX_FILE = CLIPS_DIR / "index.json"
WHISPER_BIN = os.path.expanduser("~/.openclaw/workspace/.venv/bin/whisper")
VENV_PYTHON = os.path.expanduser("~/.openclaw/workspace/.venv/bin/python3")
CHROME_BIN = "/home/xiemingsi/.cache/ms-playwright/chromium-1208/chrome-linux64/chrome"


def slugify(text, max_len=60):
    s = re.sub(r'[^\w\s-]', '', text.lower().strip())
    s = re.sub(r'[\s_]+', '-', s)
    return s[:max_len].rstrip('-') or 'untitled'


def load_index():
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text())
    return {"clips": [], "known_tags": []}


def save_index(index):
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2))


def update_known_tags(index, tags):
    known = set(index.get("known_tags", []))
    known.update(tags or [])
    index["known_tags"] = sorted(known)


def make_meta(clip_id, url, title, author, category, tags, clip_type, clip_dir, **extra):
    now = datetime.now(CST)
    meta = {
        "id": clip_id, "url": url, "title": title or clip_id,
        "author": author, "category": category, "tags": tags or [],
        "clipped_at": now.isoformat(), "type": clip_type,
        "path": str(clip_dir.relative_to(CLIPS_DIR)), "status": "ok",
    }
    meta.update(extra)
    return meta


def generate_obsidian_index():
    """Generate _INDEX.md and _TAGS.md for Obsidian navigation."""
    index = load_index()
    clips = index["clips"]
    tags_map = {}
    now = datetime.now(CST).strftime("%Y-%m-%d %H:%M")

    cats = {}
    for c in clips:
        cat = c.get("category", "uncategorized")
        cats.setdefault(cat, []).append(c)
        for t in c.get("tags", []):
            tags_map.setdefault(t, []).append(c)

    lines = [f"# 📚 Clips Index\n", f"_Last updated: {now}_\n", f"Total: {len(clips)} clips\n"]
    for cat in sorted(cats.keys()):
        lines.append(f"\n## {cat}\n")
        for c in sorted(cats[cat], key=lambda x: x.get("clipped_at", ""), reverse=True):
            date = c.get("clipped_at", "")[:10]
            title = c.get("title", "Untitled")
            path = c.get("path", "")
            author = f" — {c['author']}" if c.get("author") else ""
            status = " ⚠️" if c.get("status") == "fetch_failed" else ""
            lines.append(f"- [{title}]({path}/content.md){author} `{date}`{status}")
    (CLIPS_DIR / "_INDEX.md").write_text("\n".join(lines) + "\n")

    tlines = [f"# 🏷️ Tags\n", f"_Last updated: {now}_\n"]
    for tag in sorted(tags_map.keys()):
        tlines.append(f"\n## #{tag}\n")
        for c in tags_map[tag]:
            date = c.get("clipped_at", "")[:10]
            title = c.get("title", "Untitled")
            path = c.get("path", "")
            tlines.append(f"- [{title}]({path}/content.md) `{date}`")
    (CLIPS_DIR / "_TAGS.md").write_text("\n".join(tlines) + "\n")


def git_auto_push(message="auto: new clip"):
    """Auto commit and push clips to GitHub for Obsidian sync."""
    if not (CLIPS_DIR / ".git").exists():
        return
    try:
        subprocess.run(["git", "add", "-A"], cwd=str(CLIPS_DIR), timeout=10)
        subprocess.run(["git", "commit", "-m", message, "--allow-empty"],
                       cwd=str(CLIPS_DIR), timeout=10, capture_output=True)
        subprocess.run(["git", "push"], cwd=str(CLIPS_DIR), timeout=30, capture_output=True)
    except Exception:
        pass


def save_clip_meta(meta, clip_dir):
    """Save meta.json, update index, generate Obsidian files, push to git."""
    (clip_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    index = load_index()
    update_known_tags(index, meta.get("tags"))
    index["clips"].append(meta)
    save_index(index)
    generate_obsidian_index()
    git_auto_push(f"clip: {meta.get('title', 'untitled')}")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


def resolve_category(clip_type, subcategory=None):
    type_map = {"article": "articles", "video": "Media/videos", "audio": "Media/Audio",
                "podcast": "Media/Audio", "image": "Media/pics", "game": "Media/Games"}
    base = type_map.get(clip_type, "articles")
    return f"{base}/{subcategory}" if subcategory else base


def make_clip_dir(category, title):
    now = datetime.now(CST)
    slug = slugify(title or 'untitled')
    clip_id = f"{now.strftime('%Y-%m-%d')}-{slug}"
    clip_dir = CLIPS_DIR / category / clip_id
    clip_dir.mkdir(parents=True, exist_ok=True)
    return clip_id, clip_dir


def is_blocked_html(html):
    markers = ['<title>Just a moment...</title>', 'challenge-platform', 'cf_chl_opt',
               'Performing security verification', 'Enable JavaScript and cookies to continue',
               'Attention Required! | Cloudflare', 'cf-browser-verification', 'hCaptcha']
    return any(m in html for m in markers)


def html_to_markdown(html, url=None):
    """Convert HTML to well-formatted markdown using markdownify + BeautifulSoup."""
    try:
        sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/.venv/lib/python3.14/site-packages"))
        from bs4 import BeautifulSoup
        from markdownify import markdownify as md

        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content elements
        for tag in soup.find_all(["nav", "header", "footer", "script", "style", "noscript",
                                   "iframe", "svg", "form"]):
            tag.decompose()
        for tag in soup.find_all(class_=re.compile(r"nav|menu|sidebar|footer|header|comment|ad-|ads-|banner")):
            tag.decompose()

        # Try to find article content
        article = (soup.find("article") or soup.find(class_=re.compile(r"post-content|article|entry-content|content-body"))
                   or soup.find("main") or soup.body or soup)

        result = md(str(article), heading_style="ATX", code_language_callback=lambda el: "",
                    strip=["img"] if not article.find("img") else [])

        # Clean up excessive blank lines
        result = re.sub(r'\n{4,}', '\n\n\n', result)
        return result.strip()
    except Exception as e:
        return f"<!-- html_to_markdown failed: {e} -->\n" + html[:5000]


def fetch_with_stealth_browser(url, html_file, screenshot_file=None):
    """Fetch page using Xvfb + undetected-chromedriver, with optional full-page screenshot."""
    if not Path(VENV_PYTHON).exists() or not Path(CHROME_BIN).exists():
        return False

    sc_path = str(screenshot_file) if screenshot_file else "/dev/null"
    script = f'''
import sys, time, os, subprocess
xvfb = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1920x1080x24"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.environ["DISPLAY"] = ":99"
time.sleep(1)
try:
    import undetected_chromedriver as uc
    options = uc.ChromeOptions()
    options.binary_location = "{CHROME_BIN}"
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=zh-CN,zh")
    driver = uc.Chrome(options=options)
    driver.get("{url}")
    for i in range(30):
        if "Just a moment" not in driver.title:
            break
        time.sleep(2)
    with open("{html_file}", "w") as f:
        f.write(driver.page_source)
    sc = "{sc_path}"
    if sc != "/dev/null":
        total_h = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(1920, min(total_h + 200, 32000))
        time.sleep(1)
        driver.save_screenshot(sc)
    driver.quit()
except Exception as e:
    print(f"stealth error: {{e}}", file=sys.stderr)
finally:
    xvfb.terminate()
'''
    try:
        subprocess.run([VENV_PYTHON, "-c", script], timeout=120, capture_output=True)
        if html_file.exists() and html_file.stat().st_size > 500:
            html = html_file.read_text(errors='replace')
            if not is_blocked_html(html):
                return True
    except Exception:
        pass
    return False


def download_images(html, clip_dir, url):
    """Download images from HTML and return mapping of remote→local paths."""
    img_dir = clip_dir / "images"
    img_urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
    downloaded = {}
    if not img_urls:
        return downloaded
    img_dir.mkdir(exist_ok=True)
    for i, img_url in enumerate(img_urls[:50]):
        if img_url.startswith('data:'):
            continue
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            p = urlparse(url)
            img_url = f"{p.scheme}://{p.netloc}{img_url}"
        ext = (Path(urlparse(img_url).path).suffix or '.jpg').split('?')[0][:5]
        img_name = f"img_{i:03d}{ext}"
        try:
            subprocess.run(["curl", "-sL", "-o", str(img_dir / img_name), img_url],
                           timeout=30, check=True)
            downloaded[img_url] = f"images/{img_name}"
        except Exception:
            pass
    return downloaded


def clip_article(url, title=None, category="articles", tags=None, author=None, source=None):
    """Clip an article: fetch HTML, convert to markdown, download images, take screenshot."""
    if source:
        category = f"{category}/{source}"
    clip_id, clip_dir = make_clip_dir(category, title)
    html_file = clip_dir / "raw.html"
    screenshot_file = clip_dir / "screenshot.png"

    # Step 1: Try curl
    subprocess.run(["curl", "-sL", "-o", str(html_file), url], timeout=60)
    curl_ok = html_file.exists() and html_file.stat().st_size > 100

    if curl_ok:
        html = html_file.read_text(errors='replace')
        if is_blocked_html(html):
            curl_ok = False

    # Step 2: If curl failed, try stealth browser (with screenshot)
    if not curl_ok:
        if not fetch_with_stealth_browser(url, html_file, screenshot_file):
            meta = make_meta(clip_id, url, title, author, category, tags, "article", clip_dir,
                             status="fetch_failed", fail_reason="All fetch methods failed")
            save_clip_meta(meta, clip_dir)
            return meta
        html = html_file.read_text(errors='replace')
    else:
        # curl succeeded — still take screenshot for visual reference if stealth browser available
        fetch_with_stealth_browser(url, Path("/dev/null"), screenshot_file)

    # Step 3: Download images
    downloaded = download_images(html, clip_dir, url)

    # Step 4: Convert HTML to markdown
    markdown = html_to_markdown(html, url)

    # Replace remote image URLs with local paths in markdown
    for remote, local in downloaded.items():
        markdown = markdown.replace(remote, local)

    # Step 5: Write content.md with YAML frontmatter
    now = datetime.now(CST)
    frontmatter = f"""---
title: "{(title or clip_id).replace('"', '\\"')}"
url: {url}
author: {author or 'unknown'}
clipped_at: {now.isoformat()}
tags: [{', '.join(tags or [])}]
source: {source or ''}
---

"""
    (clip_dir / "content.md").write_text(frontmatter + markdown)

    content_size = (clip_dir / "content.md").stat().st_size
    images_size = sum(f.stat().st_size for f in (clip_dir / "images").glob("*")) if (clip_dir / "images").exists() else 0
    has_screenshot = screenshot_file.exists() and screenshot_file.stat().st_size > 0

    meta = make_meta(clip_id, url, title, author, category, tags, "article", clip_dir,
                     content_size=content_size, images_count=len(downloaded),
                     images_size=images_size, has_screenshot=has_screenshot)
    if source:
        meta["source"] = source
    save_clip_meta(meta, clip_dir)
    return meta


def clip_media(url, title=None, category=None, tags=None, author=None, media_type="video"):
    """Clip video or audio via yt-dlp."""
    if not category:
        category = resolve_category(media_type)
    clip_id, clip_dir = make_clip_dir(category, title)

    try:
        r = subprocess.run(["yt-dlp", "--dump-json", "--no-download", url],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            info = json.loads(r.stdout)
            title = title or info.get("title")
            author = author or info.get("uploader") or info.get("channel")
    except Exception:
        pass

    out_tpl = str(clip_dir / "%(title).80s.%(ext)s")
    if media_type in ("audio", "podcast"):
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "--write-thumbnail", "-o", out_tpl, url]
    else:
        cmd = ["yt-dlp", "-f", "best[height<=1080]", "--write-thumbnail",
               "--write-subs", "--sub-langs", "zh.*,en.*", "-o", out_tpl, url]

    ret = subprocess.run(cmd, timeout=600)
    if ret.returncode != 0:
        ext = "mp3" if media_type in ("audio", "podcast") else "mp4"
        subprocess.run(["curl", "-sL", "-o", str(clip_dir / f"media.{ext}"), url], timeout=300)

    total_size = sum(f.stat().st_size for f in clip_dir.rglob("*") if f.is_file())
    if total_size == 0:
        meta = make_meta(clip_id, url, title, author, category, tags, media_type, clip_dir,
                         status="fetch_failed")
        save_clip_meta(meta, clip_dir)
        return meta

    meta = make_meta(clip_id, url, title, author, category, tags, media_type, clip_dir,
                     content_size=total_size)
    save_clip_meta(meta, clip_dir)
    return meta


def transcribe(clip_path):
    """Transcribe audio in a clip directory using whisper."""
    clip_dir = CLIPS_DIR / clip_path
    audio_files = list(clip_dir.glob("*.mp3")) + list(clip_dir.glob("*.m4a")) + list(clip_dir.glob("*.ogg")) + list(clip_dir.glob("*.wav"))
    if not audio_files:
        print(json.dumps({"error": "no audio file found"}))
        return
    audio = audio_files[0]
    cmd = [WHISPER_BIN, str(audio), "--model", "small", "--language", "zh",
           "--output_dir", str(clip_dir), "--output_format", "txt"]
    subprocess.run(cmd, check=True, timeout=1200)
    txt_files = list(clip_dir.glob("*.txt"))
    if txt_files:
        txt_files[0].rename(clip_dir / "transcript.md")
    meta_file = clip_dir / "meta.json"
    if meta_file.exists():
        meta = json.loads(meta_file.read_text())
        meta["transcribed"] = True
        meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    print(json.dumps({"status": "transcribed", "path": clip_path}))


def list_clips(category=None, tag=None, content_type=None, limit=20):
    index = load_index()
    clips = index["clips"]
    if category:
        clips = [c for c in clips if c.get("category", "").startswith(category)]
    if tag:
        clips = [c for c in clips if tag in c.get("tags", [])]
    if content_type:
        clips = [c for c in clips if c.get("type") == content_type]
    for c in clips[-limit:]:
        status = " ⚠️FAILED" if c.get("status") == "fetch_failed" else ""
        print(f"[{c.get('type','?'):8s}] {c.get('clipped_at','')[:10]} | {c.get('title','')}{status} | {c.get('url','')}")


def list_tags():
    print(json.dumps(load_index().get("known_tags", []), ensure_ascii=False))


def list_subcategories(base="articles"):
    base_dir = CLIPS_DIR / base
    if not base_dir.exists():
        print("[]")
        return
    subs = sorted([d.name for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith("20")])
    print(json.dumps(subs, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description="Web Clipper")
    sub = p.add_subparsers(dest="command")

    cp = sub.add_parser("clip")
    cp.add_argument("url")
    cp.add_argument("--type", choices=["article", "video", "audio", "podcast", "image"], default="article")
    cp.add_argument("--title")
    cp.add_argument("--category")
    cp.add_argument("--subcategory", help="Subfolder under base category")
    cp.add_argument("--tags", nargs="*", default=[])
    cp.add_argument("--author")
    cp.add_argument("--source", help="Content source (e.g. NodeSeek)")

    tp = sub.add_parser("transcribe")
    tp.add_argument("clip_path")

    lp = sub.add_parser("list")
    lp.add_argument("--category")
    lp.add_argument("--tag")
    lp.add_argument("--type")
    lp.add_argument("--limit", type=int, default=20)

    sub.add_parser("tags")

    sp = sub.add_parser("subcategories")
    sp.add_argument("--base", default="articles")

    args = p.parse_args()

    if args.command == "clip":
        cat = args.category or resolve_category(args.type, args.subcategory)
        if args.type == "article":
            clip_article(args.url, args.title, cat, args.tags, args.author, args.source)
        else:
            clip_media(args.url, args.title, cat, args.tags, args.author, args.type)
    elif args.command == "transcribe":
        transcribe(args.clip_path)
    elif args.command == "list":
        list_clips(args.category, args.tag, args.type, args.limit)
    elif args.command == "tags":
        list_tags()
    elif args.command == "subcategories":
        list_subcategories(args.base)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
