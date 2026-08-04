"""啤酒百科 — 随机啤酒信息

命令：
  /啤酒       — 随机啤酒
"""

import asyncio
import json
import random
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("啤酒百科")

# ── 常量定义 ──
API_URL = "https://api.sampleapis.com/beers/ale"
TIMEOUT = 15

# ── 模块级状态 ──
_beers: Optional[list] = None


def _fetch() -> list:
    """获取啤酒列表"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


@on_command("/啤酒", "/beer", "/来瓶啤酒")
@plugin_handler
async def handle_beer(ctx: PluginContext):
    """随机啤酒"""
    global _beers
    try:
        if _beers is None:
            _beers = await asyncio.to_thread(_fetch)
        if not _beers:
            await ctx.reply("😢 获取失败，请稍后再试")
            return
        b = random.choice(_beers)
        name = b.get("name", "")
        price = b.get("price", "")
        rating = b.get("rating", {})
        rating_avg = rating.get("average", "?")
        await ctx.reply(
            f"🍺 {name}\n"
            f"━━━━━━━━━━━━\n"
            f"💲 价格: {price}\n"
            f"⭐ 评分: {rating_avg}/5\n"
            f"🏭 酒厂: {b.get('brewery', '未知')}\n"
            f"🍾 酒精度: {b.get('alcohol', '?')}\n"
            f"💡 /啤酒 再来一瓶"
        )
    except Exception as e:
        logger.error(f"啤酒获取失败: {e}")
        await ctx.reply("😢 获取失败，请稍后再试")
