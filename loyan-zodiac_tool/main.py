"""生肖查询 — 年份生肖/出生年份

命令：
  /生肖 1996      — 查生肖
  /生肖 属马      — 查年份
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("生肖查询")

# ── 常量定义 ──
ZODIAC = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]
BASE_YEAR = 2020  # 2020 = 鼠年


@on_command("/生肖", "/生肖查询", "/zodiac")
@plugin_handler
async def handle_zodiac(ctx: PluginContext):
    """生肖查询"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    arg = parts[1].strip() if len(parts) > 1 else ""

    if not arg:
        await ctx.reply("🐉 用法：\n/生肖 1996 查生肖\n/生肖 属马 查年份")
        return

    if arg.isdigit():
        year = int(arg)
        sign = ZODIAC[(year - BASE_YEAR) % 12]
        await ctx.reply(f"🐉 {year} 年是**{sign}**年")
    elif arg.startswith("属"):
        sign = arg[1]
        if sign not in ZODIAC:
            await ctx.reply("❌ 未识别的生肖")
            return
        years = [str(y) for y in range(1970, 2031) if ZODIAC[(y - BASE_YEAR) % 12] == sign]
        await ctx.reply(f"🐉 属{sign}的年份: {', '.join(years[-8:])}")
    else:
        await ctx.reply("❌ 用法：/生肖 1996 或 /生肖 属马")
