"""石头剪刀布 — 与机器人猜拳

命令：
  /猜拳 <石头|剪刀|布>     — 猜拳
  /猜拳                    — 随机出
"""

import random

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("石头剪刀布")

# ── 常量定义 ──
CHOICES = {"石头": 0, "剪刀": 1, "布": 2}
NAMES = {0: "🪨 石头", 1: "✂️ 剪刀", 2: "📄 布"}
# 胜关系：i 胜 (i+1)%3 中谁
# 石头(0)胜剪刀(1)，剪刀(1)胜布(2)，布(2)胜石头(0)


def _result(user: int, bot: int) -> str:
    """判断结果"""
    if user == bot:
        return "🤝 平局！"
    if (user == 0 and bot == 1) or (user == 1 and bot == 2) or (user == 2 and bot == 0):
        return "🎉 你赢了！"
    return "🤖 机器人赢了！"


@on_command("/猜拳", "/石头剪刀布", "/rps")
@plugin_handler
async def handle_rps(ctx: PluginContext):
    """猜拳"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    user_choice = parts[1].strip() if len(parts) > 1 else ""

    if user_choice and user_choice not in CHOICES:
        await ctx.reply("❌ 只能出：石头 / 剪刀 / 布")
        return

    if not user_choice:
        user_choice = random.choice(list(CHOICES.keys()))

    user = CHOICES[user_choice]
    bot = random.randint(0, 2)
    await ctx.reply(
        f"🎮 猜拳\n"
        f"━━━━━━━━━━━━\n"
        f"👤 你: {NAMES[user]}\n"
        f"🤖 机器人: {NAMES[bot]}\n"
        f"━━━━━━━━━━━━\n"
        f"{_result(user, bot)}"
    )
