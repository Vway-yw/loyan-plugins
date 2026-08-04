"""咖啡百科 — 随机咖啡/查询咖啡

命令：
  /咖啡       — 随机咖啡
"""

import asyncio
import json
import random
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("咖啡百科")

# ── 常量定义 ──
API_URL = "https://api.sampleapis.com/coffee/hot"
TIMEOUT = 15

# ── 模块级状态 ──
_coffees: Optional[list] = None


def _fetch() -> list:
    """获取咖啡列表"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


@on_command("/咖啡", "/coffee", "/来杯咖啡")
@plugin_handler
async def handle_coffee(ctx: PluginContext):
    """随机咖啡"""
    global _coffees
    try:
        if _coffees is None:
            _coffees = await asyncio.to_thread(_fetch)
        if not _coffees:
            await ctx.reply("😢 获取失败，请稍后再试")
            return
        c = random.choice(_coffees)
        title = c.get("title", "")
        desc = c.get("description", "")[:100]
        ingredients = ", ".join(c.get("ingredients", [])[:5])
        await ctx.reply(
            f"☕ {title}\n"
            f"━━━━━━━━━━━━\n"
            f"📝 {desc}\n"
            f"🧪 原料: {ingredients}\n"
            f"💡 /咖啡 再来一杯"
        )
    except Exception as e:
        logger.error(f"咖啡获取失败: {e}")
        await ctx.reply("😢 获取失败，请稍后再试")
