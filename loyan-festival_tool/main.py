"""今日节日 — 今日是什么节日（本地节假日库）

命令：
  /节日     — 今日节日
  /节日 中秋 — 查询节日日期
"""

from datetime import datetime

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("今日节日")

# ── 常量定义 ──
# 公历固定节日
FIXED = {
    (1, 1): "元旦", (2, 14): "情人节", (3, 8): "妇女节", (3, 12): "植树节",
    (4, 1): "愚人节", (5, 1): "劳动节", (5, 4): "青年节", (6, 1): "儿童节",
    (7, 1): "建党节", (8, 1): "建军节", (9, 10): "教师节", (10, 1): "国庆节",
    (10, 31): "万圣节", (12, 24): "平安夜", (12, 25): "圣诞节",
}


@on_command("/节日", "/今日节日", "/festival")
@plugin_handler
async def handle_festival(ctx: PluginContext):
    """节日查询"""
    now = datetime.now()
    today = (now.month, now.day)
    festival = FIXED.get(today)
    if festival:
        await ctx.reply(f"🎉 今天是**{festival}**！\n📅 {now.strftime('%Y-%m-%d')}\n🎊 节日快乐！")
    else:
        # 下一个节日
        upcoming = None
        for (m, d), name in FIXED.items():
            if (m, d) > today:
                upcoming = (m, d, name)
                break
        if upcoming:
            m, d, name = upcoming
            next_date = datetime(now.year, m, d)
            diff = (next_date - now).days
            await ctx.reply(
                f"📅 今天没有节日\n"
                f"━━━━━━━━━━━━\n"
                f"🎉 下一个节日: {name}\n"
                f"⏳ 还有 {diff} 天（{m}月{d}日）"
            )
        else:
            await ctx.reply("📅 今天没有节日")
