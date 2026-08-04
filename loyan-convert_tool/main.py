"""单位转换 — 长度/重量/温度/速度单位换算

命令：
  /转换 100km m         — 公里转米
  /转换 1kg g           — 千克转克
  /转换 36.5c f         — 摄氏转华氏
  /转换 100kmh ms       — 公里时转米秒
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("单位转换")

# ── 常量定义 ──
# 长度单位：基准 = 米
LENGTH = {
    "km": 1000.0, "m": 1.0, "cm": 0.01, "mm": 0.001,
    "mile": 1609.344, "yard": 0.9144, "foot": 0.3048, "inch": 0.0254,
    "里": 500.0, "丈": 3.33333, "尺": 0.33333, "寸": 0.03333,
}
# 重量单位：基准 = 千克
WEIGHT = {
    "t": 1000.0, "kg": 1.0, "g": 0.001, "mg": 1e-6,
    "lb": 0.453592, "oz": 0.0283495, "斤": 0.5, "两": 0.05,
}
# 速度单位：基准 = 米/秒
SPEED = {
    "kmh": 0.277778, "ms": 1.0, "mph": 0.44704, "knot": 0.514444,
}
# 温度特殊处理
TEMP = {"c", "f", "k"}


def _convert_temp(value: float, fr: str, to: str) -> float:
    """温度转换"""
    if fr == "c":
        c = value
    elif fr == "f":
        c = (value - 32) * 5 / 9
    else:
        c = value - 273.15
    if to == "c":
        return c
    if to == "f":
        return c * 9 / 5 + 32
    return c + 273.15


@on_command("/转换", "/换算", "/单位换算")
@plugin_handler
async def handle_convert(ctx: PluginContext):
    """单位转换"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split()
    if len(parts) < 3:
        await ctx.reply(
            "📏 单位转换\n"
            "━━━━━━━━━━━━\n"
            "📐 长度: km m cm mm mile foot inch 里 丈 尺 寸\n"
            "⚖️ 重量: t kg g mg lb oz 斤 两\n"
            "🌡️ 温度: c f k\n"
            "🚀 速度: kmh ms mph knot\n"
            "📖 例：/转换 100km m /转换 36.5c f"
        )
        return

    try:
        value = float(parts[1])
    except ValueError:
        await ctx.reply("❌ 数值格式错误")
        return
    fr = parts[2].lower()
    to = parts[3].lower() if len(parts) > 3 else ""

    # 确定单位类别
    if fr in LENGTH and to in LENGTH:
        result = value * LENGTH[fr] / LENGTH[to]
        cat = "📐 长度"
    elif fr in WEIGHT and to in WEIGHT:
        result = value * WEIGHT[fr] / WEIGHT[to]
        cat = "⚖️ 重量"
    elif fr in SPEED and to in SPEED:
        result = value * SPEED[fr] / SPEED[to]
        cat = "🚀 速度"
    elif fr in TEMP and to in TEMP:
        result = _convert_temp(value, fr, to)
        cat = "🌡️ 温度"
    else:
        await ctx.reply(f"❌ 无法转换 {fr} -> {to}\n支持：{' '.join(list(LENGTH) + list(WEIGHT) + list(SPEED) + list(TEMP))}")
        return

    result_str = f"{result:,.4f}".rstrip("0").rstrip(".")
    await ctx.reply(f"{cat} 转换\n━━━━━━━━━━━━\n{value:g} {fr} = {result_str} {to}")
