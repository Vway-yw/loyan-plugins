"""随机颜色 — 生成随机颜色代码

命令：
  /颜色       — 随机颜色
"""

import random

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("随机颜色")

# ── 常量定义 ──
COLOR_NAMES = [
    "红色", "橙色", "黄色", "绿色", "青色", "蓝色", "紫色",
    "粉色", "棕色", "灰色", "白色", "黑色", "金色", "银色",
]


@on_command("/颜色", "/随机颜色", "/color")
@plugin_handler
async def handle_color(ctx: PluginContext):
    """随机颜色"""
    hex_code = "#{:06X}".format(random.randint(0, 0xFFFFFF))
    r, g, b = int(hex_code[1:3], 16), int(hex_code[3:5], 16), int(hex_code[5:7], 16)
    name = random.choice(COLOR_NAMES)
    await ctx.reply(
        f"🎨 随机颜色\n"
        f"━━━━━━━━━━━━\n"
        f"🏷️ 名称: {name}\n"
        f"🔢 HEX: {hex_code}\n"
        f"🎯 RGB: ({r}, {g}, {b})\n"
        f"💡 CSS 可直接使用 {hex_code}"
    )
