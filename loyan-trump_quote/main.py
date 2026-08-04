"""川普语录 — 随机川普名言

命令：
  /川普     — 随机川普语录
"""

import asyncio
import json
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("川普语录")

# ── 常量定义 ──
API_URL = "https://api.whatdoestrumpthink.com/api/v1/quotes/random"
TIMEOUT = 15


def _fetch() -> Optional[str]:
    """获取随机川普语录"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("message")


@on_command("/川普", "/川普语录", "/trump")
@plugin_handler
async def handle_trump(ctx: PluginContext):
    """随机川普语录"""
    try:
        quote = await asyncio.to_thread(_fetch)
        if not quote:
            await ctx.reply("😢 获取失败，请稍后再试")
            return
        await ctx.reply(f"🗽 川普语录\n━━━━━━━━━━━━\n💬 \"{quote}\"\n—— 唐纳德·特朗普")
    except Exception as e:
        logger.error(f"川普语录获取失败: {e}")
        await ctx.reply("😢 获取失败，请稍后再试")
