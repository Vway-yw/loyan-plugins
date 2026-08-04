"""无聊事实 — 随机有趣冷知识

命令：
  /冷知识     — 随机冷知识
  /fact       — 同 /冷知识
"""

import asyncio
import json
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("冷知识")

# ── 常量定义 ──
API_URL = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
TIMEOUT = 15


def _fetch() -> Optional[str]:
    """获取随机冷知识"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("text")


@on_command("/冷知识", "/fact", "/无聊事实")
@plugin_handler
async def handle_fact(ctx: PluginContext):
    """随机冷知识"""
    try:
        fact = await asyncio.to_thread(_fetch)
        if not fact:
            await ctx.reply("😢 获取失败，请稍后再试")
            return
        await ctx.reply(f"🤓 冷知识\n━━━━━━━━━━━━\n💡 {fact}")
    except Exception as e:
        logger.error(f"冷知识获取失败: {e}")
        await ctx.reply("😢 获取失败，请稍后再试")
