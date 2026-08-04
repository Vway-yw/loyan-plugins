"""NASA 每日一图 — 获取 NASA 每日天文图片与说明

命令：
  /nasa        — 今日天文图片
  /nasa 日期   — 指定日期（如 /nasa 2026-08-01）
"""

import asyncio
import json
import os
import secrets
import time
import urllib.request
from typing import Dict, Optional

from graci import on_command, plugin_handler, PluginContext
from graci import get_logger, LoyanImage, loyan_send_msg

logger = get_logger("NASA每日一图")

# ── 常量定义 ──
API_URL = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY{date}"
TIMEOUT = 20
CACHE_TTL = 3600
UA = "Mozilla/5.0 (compatible; LoyanBot/1.0)"

# ── 模块级状态 ──
_cache: Dict[str, tuple] = {}


def _fetch(date: str = "") -> Optional[Dict]:
    """请求 NASA APOD API"""
    url = API_URL.format(date=f"&date={date}" if date else "")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


async def _get_apod(date: str = "") -> Optional[Dict]:
    """获取每日一图（带缓存）"""
    now = time.time()
    key = date or "today"
    cached = _cache.get(key)
    if cached and now - cached[0] < CACHE_TTL:
        return cached[1]
    data = await asyncio.to_thread(_fetch, date)
    if data and data.get("url"):
        _cache[key] = (now, data)
        return data
    return None


@on_command("/nasa", "/每日一图", "/天文")
@plugin_handler
async def handle_nasa(ctx: PluginContext):
    """获取 NASA 每日天文图片"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    date = parts[1].strip() if len(parts) > 1 else ""

    await ctx.reply("🛰️ 正在获取 NASA 每日一图...")
    data = await _get_apod(date)
    if not data:
        await ctx.reply("😢 获取失败，请检查日期格式（如 2026-08-01）")
        return

    title = data.get("title", "每日一图")
    explanation = data.get("explanation", "")
    media_type = data.get("media_type", "image")
    url = data.get("url", "")
    hdurl = data.get("hdurl", "") or url
    date_str = data.get("date", "")

    lines = [f"🛰️ NASA 每日一图 · {date_str}", "━━━━━━━━━━━━", f"📌 {title}"]
    if explanation:
        exp = explanation[:200]
        lines.append(f"📝 {exp}{'…' if len(explanation) > 200 else ''}")

    # 图片类型直接发送图片
    if media_type == "image":
        try:
            img = await asyncio.to_thread(_download, hdurl)
            if img:
                temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
                os.makedirs(temp_dir, exist_ok=True)
                path = os.path.join(temp_dir, f"nasa_{secrets.token_hex(4)}.jpg")
                with open(path, "wb") as f:
                    f.write(img)
                await ctx.reply("\n".join(lines))
                await ctx.send(LoyanImage(file_path=path))
                return
        except Exception as e:
            logger.error(f"图片下载失败: {e}")
    await ctx.reply("\n".join(lines))


def _download(url: str) -> bytes:
    """下载图片"""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()
