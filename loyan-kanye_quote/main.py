"""Kanye 语录 — 随机 Kanye West 名言

命令：
  /kanye     — 随机 Kanye 语录
"""

import asyncio
import json
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("Kanye语录")

# ── 常量定义 ──
API_URL = "https://api.kanye.rest/"
TIMEOUT = 15


def _fetch() -> Optional[str]:
    """获取随机 Kanye 语录"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("quote")


@on_command("/kanye", "/侃爷", "/kanye语录")
@plugin_handler
async def handle_kanye(ctx: PluginContext):
    """随机 Kanye 语录"""
    try:
        quote = await asyncio.to_thread(_fetch)
        if not quote:
            await ctx.reply("😢 获取失败，请稍后再试")
            return
        await ctx.reply(f"🎤 Kanye 语录\n━━━━━━━━━━━━\n💬 \"{quote}\"\n—— Kanye West")
    except Exception as e:
        logger.error(f"Kanye 获取失败: {e}")
        await ctx.reply("😢 获取失败，请稍后再试")
