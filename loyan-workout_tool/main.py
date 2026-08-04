"""健身动作 — 查询健身动作（含中文翻译）

命令：
  /健身       — 随机健身动作
"""

import asyncio
import json
import random
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("健身动作")

# ── 常量定义 ──
API_URL = "https://wger.de/api/v2/exercise/?format=json&limit=100"
TIMEOUT = 15

# ── 模块级状态 ──
_exercises: Optional[list] = None

# 英文动作名常见中文翻译
EQUIP_ZH = {
    "barbell": "杠铃", "dumbbell": "哑铃", "machine": "器械", "body only": "自重",
    "cable": "绳索", "kettlebells": "壶铃", "other": "其他", "bands": "弹力带",
}


def _fetch() -> list:
    """获取健身动作"""
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8")).get("results", [])


@on_command("/健身", "/健身动作", "/workout")
@plugin_handler
async def handle_workout(ctx: PluginContext):
    """随机健身动作"""
    global _exercises
    try:
        if _exercises is None:
            _exercises = await asyncio.to_thread(_fetch)
        if not _exercises:
            await ctx.reply("😢 获取失败，请稍后再试")
            return
        ex = random.choice(_exercises)
        name = ex.get("name", "")
        desc = ex.get("description", "")
        # 去除 HTML 标签
        import re
        desc = re.sub(r"<[^>]+>", "", desc).strip()[:100]
        cat = ex.get("category", {}).get("name", "")
        equip = ex.get("equipment", {}).get("name", "")
        equip_zh = EQUIP_ZH.get(equip.lower(), equip)
        await ctx.reply(
            f"💪 {name}\n"
            f"━━━━━━━━━━━━\n"
            f"📌 类别: {cat}\n"
            f"🏋️ 器械: {equip_zh}\n"
            f"📝 {desc or '（无描述）'}\n"
            f"💡 /健身 换一个"
        )
    except Exception as e:
        logger.error(f"健身获取失败: {e}")
        await ctx.reply("😢 获取失败，请稍后再试")
