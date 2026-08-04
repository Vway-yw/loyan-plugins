"""纪念日计算 — 计算恋爱/认识天数

命令：
  /在一起 2023-01-01     — 在一起天数
  /纪念 2023-01-01       — 同
"""

from datetime import datetime

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("纪念日")


def _parse(s: str):
    """解析日期"""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


@on_command("/在一起", "/恋爱天数", "/纪念")
@plugin_handler
async def handle_anniv(ctx: PluginContext):
    """纪念日计算"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    if not arg:
        await ctx.reply("💑 用法：/在一起 <日期>\n例：/在一起 2023-01-01")
        return

    start = _parse(arg)
    if not start:
        await ctx.reply("❌ 日期格式错误（如 2023-01-01）")
        return

    now = datetime.now()
    days = (now - start).days
    if days < 0:
        await ctx.reply("❌ 日期不能是未来")
        return

    weeks = days // 7
    months = days // 30
    years = days // 365
    hearts = "💕" * min(5, max(1, days // 100 + 1))
    await ctx.reply(
        f"💑 纪念日\n"
        f"━━━━━━━━━━━━\n"
        f"📅 起始: {start.strftime('%Y-%m-%d')}\n"
        f"📊 已在一起 **{days}** 天\n"
        f"⏳ ≈ {years} 年 {months % 12} 个月\n"
        f"📆 ≈ {weeks} 周\n"
        f"{hearts}"
    )
