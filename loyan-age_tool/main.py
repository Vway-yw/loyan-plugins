"""年龄计算 — 根据生日计算年龄

命令：
  /年龄 1996-05-20     — 计算年龄
"""

from datetime import datetime

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("年龄计算")


def _parse(s: str):
    """解析日期"""
    for fmt in ("%Y-%m-%d", "%Y/%m-%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _calc(birth: datetime) -> tuple:
    """计算年龄（年/月/天）"""
    now = datetime.now()
    years = now.year - birth.year
    months = now.month - birth.month
    days = now.day - birth.day
    if days < 0:
        months -= 1
        import calendar
        days += calendar.monthrange(now.year if months >= 0 else now.year - 1, (now.month - 1) or 12)[1]
    if months < 0:
        years -= 1
        months += 12
    total_days = (now - birth).days
    return years, months, days, total_days


@on_command("/年龄", "/周岁", "/age")
@plugin_handler
async def handle_age(ctx: PluginContext):
    """年龄计算"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    if not arg:
        await ctx.reply("🎂 用法：/年龄 <生日>\n例：/年龄 1996-05-20")
        return

    birth = _parse(arg)
    if not birth:
        await ctx.reply("❌ 日期格式错误（如 1996-05-20）")
        return

    years, months, days, total = _calc(birth)
    await ctx.reply(
        f"🎂 年龄计算\n"
        f"━━━━━━━━━━━━\n"
        f"📅 生日: {birth.strftime('%Y-%m-%d')}\n"
        f"🎂 年龄: {years} 岁 {months} 个月 {days} 天\n"
        f"📊 总天数: {total:,} 天\n"
        f"🎈 出生星期: {'一二三四五六日'[birth.weekday()]}"
    )
