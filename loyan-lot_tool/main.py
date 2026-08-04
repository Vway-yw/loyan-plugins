"""掷签/抽签 — 随机抽签（大吉/中吉/小吉等）

命令：
  /抽签     — 抽一支签
  /签       — 同 /抽签
"""

import random

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("抽签")

# ── 常量定义 ──
SIGNS = [
    ("大吉", "🌈 万事顺遂，心想事成！"),
    ("中吉", "✨ 稳步向前，机遇将至。"),
    ("小吉", "🌱 小有所获，保持耐心。"),
    ("吉", "🌞 一切正常，宜努力。"),
    ("末吉", "🌤️ 平平稳稳，勿骄勿躁。"),
    ("小凶", "🌧️ 小心行事，谨慎为上。"),
    ("凶", "⛈️ 遇事三思，避其锋芒。"),
    ("大凶", "🌀 静待时机，韬光养晦。"),
]
FORTUNES = ["财运", "事业", "爱情", "健康", "学业", "人际"]


@on_command("/抽签", "/签", "/运势签")
@plugin_handler
async def handle_lot(ctx: PluginContext):
    """随机抽签"""
    grade, advice = random.choice(SIGNS)
    fortune = random.choice(FORTUNES)
    await ctx.reply(
        f"🎋 抽签结果\n"
        f"━━━━━━━━━━━━\n"
        f"🏮 签文: {grade}\n"
        f"📜 提示: {advice}\n"
        f"🔮 今日{fortune}: {'★★★★★' if '大吉' in grade else '★★★★☆' if '吉' in grade and '末' not in grade else '★★★☆☆' if '凶' not in grade else '★★☆☆☆'}\n"
        f"💡 /抽签 再来一支"
    )
