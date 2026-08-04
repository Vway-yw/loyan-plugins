"""一言 — 获取一言/名言/诗词/动漫台词

命令：
  /一言           — 随机一言
  /一言 诗词      — 古诗词
  /一言 动漫      — 动漫台词
  /一言 名言      — 名人名言
  /一言 英文      — 英文句子
  /一言 哲学      — 哲学句子
"""

import asyncio
import json
import time
import urllib.parse
import urllib.request
from typing import Dict, Optional

from graci import on_command, plugin_handler, PluginContext
from graci import get_logger

logger = get_logger("一言")

# ── 常量定义 ──
API_URL = "https://v1.hitokoto.cn/?encode=json{ctype}"
TIMEOUT = 15
CACHE_TTL = 60

# 分类映射
TYPE_MAP = {
    "诗词": "&c=d",
    "动漫": "&c=a",
    "名言": "&c=i",
    "英文": "&c=e",
    "哲学": "&c=w",
    "网络": "&c=other",
    "文学": "&c=k",
    "影视": "&c=h",
}

# ── 模块级状态 ──
_cache: Dict[str, tuple] = {}


def _fetch(ctype: str = "") -> Optional[Dict]:
    """请求一言 API"""
    url = API_URL.format(ctype=ctype)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


@on_command("/一言", "/一言", "/语录", "/句子")
@plugin_handler
async def handle_hitokoto(ctx: PluginContext):
    """获取一言句子"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    cat = parts[1].strip() if len(parts) > 1 else ""
    ctype = TYPE_MAP.get(cat, "")

    cache_key = cat
    now = time.time()
    cached = _cache.get(cache_key)
    if cached and now - cached[0] < CACHE_TTL:
        data = cached[1]
    else:
        try:
            data = await asyncio.to_thread(_fetch, ctype)
            if data and data.get("hitokoto"):
                _cache[cache_key] = (now, data)
        except Exception as e:
            logger.error(f"一言获取失败: {e}")
            data = None

    if not data or not data.get("hitokoto"):
        await ctx.reply("😢 获取失败，请稍后再试")
        return

    text = data["hitokoto"]
    author = data.get("from", "") or ""
    from_who = data.get("from_who", "") or ""
    if from_who:
        author = f"{from_who}（{author}）"
    lines = [f"💬 {text}"]
    if author:
        lines.append(f"—— {author}")
    if cat:
        lines.insert(0, f"📖 {cat}一言")
    await ctx.reply("\n".join(lines))
