"""土味情话 — 随机土味情话（本地库）

命令：
  /情话     — 随机土味情话
"""

import random

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("土味情话")

# ── 常量定义 ──
LOVE_LINES = [
    "你知道你和星星有什么区别吗？星星在天上，你在我心里。",
    "你知道我为什么感冒了吗？因为我对你完全没有抵抗力。",
    "我最近有点忙，忙着喜欢你。",
    "你猜我的心在哪边？左边。不对，在你那边。",
    "我喜欢你，像风走了八千里，不问归期。",
    "你的名字，是我读过最短的情诗。",
    "我想和你一起，看遍世间繁华。",
    "众生皆苦，只有你是草莓味的。",
    "你是我这一生，等了半世未拆的礼物。",
    "我对你的爱，像圆周率一样无限不循环。",
    "春风十里，不如你。",
    "遇见你之后，我的数学成绩变好了，因为你是我的一切（+∞）。",
    "你知道我最喜欢什么天气吗？有你的一天。",
    "我的心跳，在你出现的那一刻开始加速。",
    "月亮很圆，风很温柔，你很好看。",
]


@on_command("/情话", "/土味情话", "/love")
@plugin_handler
async def handle_love(ctx: PluginContext):
    """随机土味情话"""
    line = random.choice(LOVE_LINES)
    await ctx.reply(f"💕 土味情话\n━━━━━━━━━━━━\n💬 {line}\n\n💡 /情话 再来一句")
