"""幸运数字 — 今日幸运数字/抽签

命令：
  /幸运数字       — 今日幸运数字
"""

import random
from datetime import datetime

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("幸运数字")

# ── 常量定义 ──
COLORS = ["红色", "橙色", "黄色", "绿色", "青色", "蓝色", "紫色"]
DIRECTIONS = ["东", "南", "西", "北", "东南", "东北", "西南", "西北"]


@on_command("/幸运数字", "/幸运", "/lucky")
@plugin_handler
async def handle_lucky(ctx: PluginContext):
    """幸运数字"""
    now = datetime.now()
    seed = int(now.strftime("%Y%m%d"))
    rng = random.Random(seed)
    num = rng.randint(1, 99)
    color = rng.choice(COLORS)
    direction = rng.choice(DIRECTIONS)
    await ctx.reply(
        f"🍀 今日幸运\n"
        f"━━━━━━━━━━━━\n"
        f"🔢 幸运数字: {num}\n"
        f"🎨 幸运色: {color}\n"
        f"🧭 幸运方向: {direction}\n"
        f"━━━━━━━━━━━━\n"
        f"📅 {now.strftime('%Y-%m-%d')} · 每天更新"
    )
