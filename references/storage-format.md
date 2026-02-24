# Storage Format

## Directory Layout

```
~/.openclaw/workspace/clips/
├── index.json                    # Global clip index + known_tags
├── articles/
│   ├── 2026-02-24-some-title/    # 无子分类的文章直接放这里
│   │   ├── meta.json
│   │   ├── raw.html
│   │   ├── content.md
│   │   └── images/
│   ├── 微信公众号-xxx/            # 按来源分的子目录
│   │   └── 2026-02-24-article/
│   └── VPS/                      # 按主题分的子目录
│       └── 2026-02-24-guide/
└── Media/
    ├── Audio/                    # 播客、音乐等
    │   └── 2026-02-24-episode/
    │       ├── meta.json
    │       ├── *.mp3
    │       └── transcript.md     # whisper 转写（可选）
    ├── Games/
    ├── pics/
    └── videos/
        └── 2026-02-24-video/
            ├── meta.json
            ├── *.mp4
            ├── *.jpg             # 缩略图
            └── *.vtt             # 字幕
```

## index.json Schema

```json
{
  "known_tags": ["tech", "ai", "coffee"],
  "clips": [
    {
      "id": "2026-02-24-some-title",
      "url": "https://example.com/article",
      "title": "Some Title",
      "author": "Author Name",
      "category": "articles/微信公众号-xxx",
      "tags": ["tech", "ai"],
      "clipped_at": "2026-02-24T10:30:00+08:00",
      "type": "article",
      "status": "ok",
      "source": "微信公众号-xxx",
      "path": "articles/微信公众号-xxx/2026-02-24-some-title"
    }
  ]
}
```

## meta.json Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique clip ID (date-slug) |
| url | string | Original URL |
| title | string | Content title |
| author | string? | Author/uploader name |
| category | string | Storage category path |
| tags | string[] | Tags (reuse known_tags) |
| clipped_at | string | ISO 8601 timestamp (CST) |
| type | string | article/video/audio/podcast/image |
| status | string | "ok" or "fetch_failed" |
| source | string? | Content source (e.g. 微信公众号名) |
| transcribed | boolean? | Whether audio has been transcribed |
| path | string | Relative path from clips root |
