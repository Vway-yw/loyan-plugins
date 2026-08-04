"""随机用户 — 生成随机个人信息（用于测试/演示）

命令：
  /随机用户     — 生成随机用户信息
  /假人         — 同 /随机用户
"""

import asyncio
import json
import time
import urllib.request
from typing import Dict, Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("随机用户")

# ── 常量定义 ──
API_URL = "https://randomuser.me/api/"
TIMEOUT = 15
CACHE_TTL = 60


def _fetch() -> Optional[Dict]:
    """请求随机用户 API"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


@on_command("/随机用户", "/假人", "/randuser")
@plugin_handler
async def handle_randuser(ctx: PluginContext):
    """生成随机用户信息"""
    await ctx.reply("👤 正在生成随机用户...")
    try:
        data = await asyncio.to_thread(_fetch)
        if not data or not data.get("results"):
            await ctx.reply("😢 获取失败，请稍后再试")
            return
        u = data["results"][0]
        name = f"{u['name']['title']} {u['name']['first']} {u['name']['last']}"
        gender = "👨 男" if u.get("gender") == "male" else "👩 女"
        loc = u.get("location", {})
        lines = [
            "👤 随机用户信息",
            "━━━━━━━━━━━━",
            f"👤 姓名: {name}",
            f"{gender}",
            f"🇺🇸 国籍: {u.get('nat', '')}",
            f"📍 地区: {loc.get('city', '')}, {loc.get('country', '')}",
            f"📧 邮箱: {u.get('email', '')}",
            f"📱 电话: {u.get('phone', '')}",
            f"🗓️ 生日: {u.get('dob', {}).get('date', '')[:10]}",
            f"🎂 年龄: {u.get('dob', {}).get('age', '')}",
        ]
        await ctx.reply("\n".join(lines))
    except Exception as e:
        logger.error(f"随机用户获取失败: {e}")
        await ctx.reply("😢 获取失败，请稍后再试")
