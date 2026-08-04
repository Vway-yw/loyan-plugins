"""星期计算 — 日期星期/两个日期相差天数

命令：
  /星期 2026-08-04     — 查星期
  /星期 2026-08-04 2026-10-01  — 相差天数
"""

from datetime import datetime

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("星期计算")


def _parse(s: str):
    """解析日期"""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


@on_command("/星期", "/星期几", "/weekday")
@plugin_handler
async def handle_weekday(ctx: PluginContext):
    """星期/日期差计算"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)

    if len(parts) < 2:
        await ctx.reply("📅 用法：\n/星期 <日期> 查星期\n/星期 <日期> <日期> 相差天数\n例：/星期 2026-08-04")
        return

    d1 = _parse(parts[1])
    if not d1:
        await ctx.reply("❌ 日期格式错误（如 2026-08-04）")
        return

    if len(parts) > 2:
        d2 = _parse(parts[2])
        if not d2:
            await ctx.reply("❌ 第二个日期格式错误")
            return
        diff = abs((d2 - d1).days)
        await ctx.reply(f"📅 {d1.strftime('%Y-%m-%d')} 到 {d2.strftime('%Y-%m-%d')}\n━━━━━━━━━━━━\n📊 相差 **{diff}** 天")
        return

    weekday = "一二三四五六日"[d1.weekday()]
    is_weekend = "🎉 周末！" if d1.weekday() >= 5 else "💼 工作日"
    await ctx.reply(
        f"📅 {d1.strftime('%Y-%m-%d')}\n"
        f"━━━━━━━━━━━━\n"
        f"📌 星期{weekday}\n"
        f"{is_weekend}"
    )
