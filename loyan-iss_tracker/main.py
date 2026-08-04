"""ISS 定位 — 查看国际空间站实时位置

命令：
  /iss     — 国际空间站当前位置
"""

import asyncio
import json
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("ISS定位")

# ── 常量定义 ──
API_URL = "https://api.wheretheiss.at/v1/satellites/25544"
TIMEOUT = 15


def _fetch() -> Optional[dict]:
    """获取 ISS 位置"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


@on_command("/iss", "/空间站", "/国际空间站")
@plugin_handler
async def handle_iss(ctx: PluginContext):
    """查看国际空间站位置"""
    await ctx.reply("🛰️ 正在查询国际空间站位置...")
    try:
        data = await asyncio.to_thread(_fetch)
        if not data:
            await ctx.reply("😢 查询失败，请稍后再试")
            return
        lat = data.get("latitude")
        lon = data.get("longitude")
        alt = data.get("altitude")
        vel = data.get("velocity")
        await ctx.reply(
            f"🛰️ 国际空间站 ISS\n"
            f"━━━━━━━━━━━━\n"
            f"📍 纬度: {lat:.2f}°\n"
            f"📍 经度: {lon:.2f}°\n"
            f"📏 高度: {alt:.1f} km\n"
            f"🚀 速度: {vel:.2f} km/h\n"
            f"💡 地球上空约 400km 轨道运行"
        )
    except Exception as e:
        logger.error(f"ISS 查询失败: {e}")
        await ctx.reply("😢 查询失败，请稍后再试")
