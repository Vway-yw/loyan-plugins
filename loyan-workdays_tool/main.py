"""工作日计算 — 两个日期间的工作日天数

命令：
  /工作日 2026-08-01 2026-08-31     — 工作日天数
"""

from datetime import datetime, timedelta

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("工作日计算")


def _parse(s: str):
    """解析日期"""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


@on_command("/工作日", "/workdays", "/上班天数")
@plugin_handler
async def handle_workdays(ctx: PluginContext):
    """工作日计算"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)

    if len(parts) < 2:
        await ctx.reply("📅 用法：/工作日 <起始> <结束>\n例：/工作日 2026-08-01 2026-08-31")
        return

    d1 = _parse(parts[1])
    d2 = _parse(parts[2]) if len(parts) > 2 else datetime.now()
    if not d1 or not d2:
        await ctx.reply("❌ 日期格式错误（如 2026-08-01）")
        return
    if d1 > d2:
        d1, d2 = d2, d1

    workdays = 0
    weekends = 0
    cur = d1
    while cur <= d2:
        if cur.weekday() < 5:
            workdays += 1
        else:
            weekends += 1
        cur += timedelta(days=1)

    total = (d2 - d1).days + 1
    await ctx.reply(
        f"📅 工作日统计\n"
        f"━━━━━━━━━━━━\n"
        f"📆 {d1.strftime('%Y-%m-%d')} ~ {d2.strftime('%Y-%m-%d')}\n"
        f"📊 共 {total} 天\n"
        f"💼 工作日: {workdays} 天\n"
        f"🏖️ 周末: {weekends} 天"
    )
