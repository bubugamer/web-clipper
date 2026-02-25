# Web Clipper 网页收藏工具

一个本地化的网页内容收藏、归档和管理工具。支持文章、视频、播客的抓取，自动绕过 Cloudflare 防护，HTML 结构化转 Markdown，全页截图备份，Obsidian 同步。

## ✨ 特性

- **智能抓取** — curl 优先，Cloudflare 站点自动切换 Xvfb + undetected-chromedriver 绕过
- **HTML → Markdown** — 使用 markdownify 结构化转换，保留标题层级、代码块、引用、列表、图片
- **全页截图** — 自动保存长截图作为原始排版的视觉备份
- **图片本地化** — 自动下载文章配图到本地，替换远程链接
- **分类管理** — 文章按来源/主题分子目录，媒体按类型分类
- **标签系统** — 可复用标签库，自动维护 known_tags 索引
- **Obsidian 同步** — 自动生成 `_INDEX.md` 和 `_TAGS.md`，git push 到 GitHub
- **音频转写** — 集成 OpenAI Whisper，支持中英文语音转文字
- **失败兜底** — 抓取失败仍保存元信息，不丢失任何收藏请求

## 📁 目录结构

```
clips/
├── index.json              # 全局索引 + 标签库
├── _INDEX.md               # Obsidian 导航页（自动生成）
├── _TAGS.md                # 标签聚合页（自动生成）
├── .gitignore              # 排除 raw.html、大文件
├── articles/               # 文章
│   ├── 2026-02-24-标题/    # 无子分类
│   │   ├── content.md      # Markdown 正文（带 YAML frontmatter）
│   │   ├── screenshot.png  # 全页截图
│   │   ├── meta.json       # 元信息
│   │   ├── raw.html        # 原始 HTML（不同步到 Git）
│   │   └── images/         # 本地化图片
│   ├── NodeSeek/           # 按来源分子目录
│   └── 微信公众号-xxx/      # 按公众号分子目录
└── Media/
    ├── Audio/              # 播客、音乐
    ├── Games/              # 游戏相关
    ├── pics/               # 图片
    └── videos/             # 视频
```

## 🚀 使用方法

### 收藏文章

```bash
# 基本用法
python3 scripts/clip.py clip "https://example.com/article" --type article --title "文章标题" --tags tech ai

# 指定来源（自动创建子目录）
python3 scripts/clip.py clip "URL" --type article --source "NodeSeek" --title "标题"

# 指定主题子目录
python3 scripts/clip.py clip "URL" --type article --subcategory "VPS" --title "标题"
```

### 收藏视频/音频

```bash
python3 scripts/clip.py clip "URL" --type video --title "视频标题"
python3 scripts/clip.py clip "URL" --type audio --title "播客标题"
```

### 音频转写

```bash
python3 scripts/clip.py transcribe "Media/Audio/2026-02-24-episode"
```

### 查询管理

```bash
python3 scripts/clip.py list                          # 列出所有收藏
python3 scripts/clip.py list --type article --tag vps  # 按类型和标签筛选
python3 scripts/clip.py tags                           # 查看已有标签
python3 scripts/clip.py subcategories --base articles  # 查看已有子目录
```

## 🔄 抓取策略

文章抓取采用自动递进策略：

```
curl 抓取（快速）
  ↓ 检测到 Cloudflare？
Xvfb + undetected-chromedriver（非 headless，绕过反爬）
  ↓ 同时保存全页截图
HTML → markdownify 结构化转换 → content.md
  ↓ 还是失败？
保存元信息（status=fetch_failed）+ 向用户报告
```

### 转换效果对比

| 元素 | 旧版（纯文本） | 新版（markdownify） |
|------|---------------|-------------------|
| 标题 | 混在正文里 | `#### 标题层级` |
| 代码块 | 无格式 | ` ```代码块``` ` |
| 引用 | 无格式 | `> 引用块` |
| 列表 | 无格式 | `- 列表项` |
| 加粗 | 无格式 | `**加粗**` |
| 图片 | 丢失 | `![](images/img_000.png)` |

## 📋 依赖

- Python 3.10+
- `curl`, `yt-dlp`, `ffmpeg`, `Xvfb`
- Python 包（venv）：`openai-whisper`, `undetected-chromedriver`, `markdownify`
- Chromium（通过 Playwright 安装）

## 📄 License

MIT
