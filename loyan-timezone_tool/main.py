"""当前时间 — 多时区时间查询

命令：
  /时区 北京     — 北京时间
  /时区 纽约     — 纽约时间
  /时区          — 主要时区
"""

from datetime import datetime, timezone, timedelta

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("多时区")

# ── 常量定义 ──
ZONES = {
    "北京": ("Asia/Shanghai", 8), "东京": ("Asia/Tokyo", 9), "首尔": ("Asia/Seoul", 9),
    "新加坡": ("Asia/Singapore", 8), "伦敦": ("Europe/London", 1), "巴黎": ("Europe/Paris", 2),
    "纽约": ("America/New_York", -4), "洛杉矶": ("America/Los_Angeles", -7),
    "悉尼": ("Australia/Sydney", 10), "迪拜": ("Asia/Dubai", 4), "莫斯科": ("Europe/Moscow", 3),
}


@on_command("/时区", "/多时区", "/timezone")
@plugin_handler
async def handle_tz(ctx: PluginContext):
    """多时区时间"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    city = parts[1].strip() if len(parts) > 1 else ""

    if not city:
        lines = ["🌍 世界时间", "━━━━━━━━━━━━"]
        for c, (_, offset) in ZONES.items():
            t = datetime.now(timezone(timedelta(hours=offset)))
            lines.append(f"{c}: {t.strftime('%H:%M')}")
        lines.append("━━━━━━━━━━━━\n💡 /时区 北京 指定城市")
        await ctx.reply("\n".join(lines))
        return

    if city not in ZONES:
        await ctx.reply(f"❌ 未收录「{city}」\n💡 支持: {' '.join(ZONES.keys())}")
        return

    name, offset = ZONES[city]
    t = datetime.now(timezone(timedelta(hours=offset)))
    await ctx.reply(f"🌍 {city} 时间\n━━━━━━━━━━━━\n🕐 {t.strftime('%Y-%m-%d %H:%M:%S')}\n📌 UTC{offset:+d}")
