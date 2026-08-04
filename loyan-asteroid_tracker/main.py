"""小行星监测 — 查询 NASA 近地小行星数据

命令：
  /小行星          — 今日近地小行星
  /小行星 3        — 未来 3 天
"""

import asyncio
import json
import time
import urllib.request
from datetime import datetime, timedelta
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("小行星监测")

# ── 常量定义 ──
API_URL = "https://api.nasa.gov/neo/rest/v1/feed?start_date={start}&end_date={end}&api_key=DEMO_KEY"
TIMEOUT = 20


def _fetch(days: int) -> Optional[dict]:
    """获取近地小行星数据"""
    start = datetime.utcnow().strftime("%Y-%m-%d")
    end = (datetime.utcnow() + timedelta(days=days - 1)).strftime("%Y-%m-%d")
    url = API_URL.format(start=start, end=end)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


@on_command("/小行星", "/近地小行星", "/asteroid")
@plugin_handler
async def handle_asteroid(ctx: PluginContext):
    """查询近地小行星"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    days = 1
    if len(parts) > 1 and parts[1].strip().isdigit():
        days = min(max(int(parts[1].strip()), 1), 7)

    await ctx.reply("☄️ 正在查询近地小行星...")
    try:
        data = await asyncio.to_thread(_fetch, days)
        if not data or "near_earth_objects" not in data:
            await ctx.reply("😢 查询失败，请稍后再试")
            return
        neo = data["near_earth_objects"]
        total = 0
        lines = [f"☄️ 近地小行星（未来 {days} 天）", "━━━━━━━━━━━━"]
        for date in sorted(neo.keys()):
            objects = neo[date]
            total += len(objects)
            for obj in objects[:3]:
                name = obj.get("name", "")
                size = obj.get("estimated_diameter", {}).get("meters", {}).get("estimated_diameter_max", 0)
                hazard = "⚠️ 有威胁" if obj.get("is_potentially_hazardous_asteroid") else "✅ 安全"
                lines.append(f"📆 {date}")
                lines.append(f"   ☄️ {name[:40]}")
                lines.append(f"   📏 直径 ~{size:.1f}m · {hazard}")
        lines.append("━━━━━━━━━━━━")
        lines.append(f"📊 共 {total} 颗 · 数据源 NASA")
        await ctx.reply("\n".join(lines))
    except Exception as e:
        logger.error(f"小行星查询失败: {e}")
        await ctx.reply("😢 查询失败，请稍后再试")
