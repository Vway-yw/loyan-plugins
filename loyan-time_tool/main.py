"""时间工具 — 时间戳转换 / 当前时间 / 时区

命令：
  /时间             — 当前时间
  /时间戳           — 当前 Unix 时间戳
  /时间戳 1750000000 — 时间戳转日期
  /倒计时 2026-10-01 — 距目标日期的倒计时
"""

import time
from datetime import datetime

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("时间工具")


def _parse_date(s: str):
    """解析日期字符串"""
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


@on_command("/时间", "/现在时间", "/几点")
@plugin_handler
async def handle_time(ctx: PluginContext):
    """当前时间"""
    now = datetime.now()
    weekday = "一二三四五六日"[now.weekday()]
    await ctx.reply(
        f"🕐 当前时间\n"
        f"━━━━━━━━━━━━\n"
        f"📅 {now.strftime('%Y-%m-%d')} 星期{weekday}\n"
        f"⏰ {now.strftime('%H:%M:%S')}\n"
        f"💡 时间戳: {int(now.timestamp())}"
    )


@on_command("/时间戳", "/timestamp", "/ts")
@plugin_handler
async def handle_ts(ctx: PluginContext):
    """时间戳转换"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)

    if len(parts) < 2:
        ts = int(time.time())
        await ctx.reply(f"⏱️ 当前时间戳: **{ts}**\n📅 对应时间: {datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')}")
        return

    arg = parts[1].strip()
    try:
        ts = int(arg)
        if ts > 10**12:
            ts //= 1000  # 毫秒转秒
        dt = datetime.fromtimestamp(ts)
        await ctx.reply(
            f"⏱️ 时间戳转换\n"
            f"━━━━━━━━━━━━\n"
            f"🔢 时间戳: {ts}\n"
            f"📅 日期: {dt.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except (ValueError, OSError):
        await ctx.reply("❌ 时间戳格式错误（如 1750000000）")


@on_command("/倒计时", "/countdown")
@plugin_handler
async def handle_countdown(ctx: PluginContext):
    """倒计时"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    if len(parts) < 2:
        await ctx.reply("📅 用法：/倒计时 2026-10-01")
        return

    target = _parse_date(parts[1].strip())
    if not target:
        await ctx.reply("❌ 日期格式错误（如 2026-10-01）")
        return

    now = datetime.now()
    delta = target - now
    days = delta.days
    if days < 0:
        await ctx.reply(f"📅 {target.strftime('%Y-%m-%d')} 已过去 **{abs(days)}** 天")
    elif days == 0:
        await ctx.reply(f"📅 就是今天！{target.strftime('%Y-%m-%d')}")
    else:
        hours = int(delta.seconds // 3600)
        mins = int((delta.seconds % 3600) // 60)
        await ctx.reply(
            f"📅 距 {target.strftime('%Y-%m-%d')}\n"
            f"━━━━━━━━━━━━\n"
            f"⏳ 还有 **{days}** 天 {hours} 小时 {mins} 分"
        )
