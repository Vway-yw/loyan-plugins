"""今日诗词 — 获取古诗词（按分类）

命令：
  /诗词             — 随机诗词
  /诗词 山水        — 山水类诗词
  /诗词 节日        — 节日类诗词
  /诗词 爱情        — 爱情类诗词
"""

import asyncio
import json
import time
import urllib.request
from typing import Dict, Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("今日诗词")

# ── 常量定义 ──
API_URL = "https://v1.jinrishici.com/all.json{cat}"
TIMEOUT = 15
CACHE_TTL = 60

# ── 模块级状态 ──
_cache: Dict[str, tuple] = {}


def _fetch(cat: str = "") -> Optional[Dict]:
    """请求诗词 API"""
    url = API_URL.format(cat=f"?type={cat}" if cat else "")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


@on_command("/诗词", "/古诗", "/今日诗词")
@plugin_handler
async def handle_shici(ctx: PluginContext):
    """获取古诗词"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    cat = parts[1].strip() if len(parts) > 1 else ""

    await ctx.reply("📜 正在寻找诗词...")
    cache_key = cat
    now = time.time()
    cached = _cache.get(cache_key)
    if cached and now - cached[0] < CACHE_TTL:
        data = cached[1]
    else:
        try:
            data = await asyncio.to_thread(_fetch, cat)
            if data and data.get("content"):
                _cache[cache_key] = (now, data)
        except Exception as e:
            logger.error(f"诗词获取失败: {e}")
            data = None

    if not data or not data.get("content"):
        await ctx.reply("😢 获取失败，请稍后再试")
        return

    content = data["content"]
    origin = data.get("origin", "")
    author = data.get("author", "")
    category = data.get("category", "")
    lines = [f"📜 {content}"]
    lines.append(f"——《{origin}》 {author}")
    if category:
        lines.append(f"🏷️ {category}")
    await ctx.reply("\n".join(lines))
