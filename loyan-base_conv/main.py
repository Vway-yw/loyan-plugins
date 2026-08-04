"""进制转换 — 十进制/二进制/八进制/十六进制互转

命令：
  /进制 255 16     — 十进制 255 转十六进制
  /进制 1010 2     — 十进制 1010 转二进制
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("进制转换")

# ── 常量定义 ──
BASE_NAMES = {2: "二进制", 8: "八进制", 10: "十进制", 16: "十六进制"}


def _convert(value_str: str, to_base: int) -> str:
    """十进制转指定进制"""
    value = int(value_str)
    if to_base == 10:
        return str(value)
    return format(value, "b") if to_base == 2 else format(value, "o") if to_base == 8 else format(value, "X")


@on_command("/进制", "/进制转换", "/base")
@plugin_handler
async def handle_base(ctx: PluginContext):
    """进制转换"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split()

    if len(parts) < 2:
        await ctx.reply(
            "🔢 进制转换\n"
            "━━━━━━━━━━━━\n"
            "💡 /进制 <十进制数> <进制>\n"
            "🔢 支持: 2(二) 8(八) 10(十) 16(十六)\n"
            "📖 例：/进制 255 16 → FF"
        )
        return

    try:
        value = int(parts[1])
        to_base = int(parts[2]) if len(parts) > 2 else 16
    except ValueError:
        await ctx.reply("❌ 请输入数字")
        return

    if to_base not in BASE_NAMES:
        await ctx.reply("❌ 仅支持 2/8/10/16 进制")
        return

    result = _convert(str(value), to_base)
    lines = [f"🔢 {value} 的进制转换", "━━━━━━━━━━━━"]
    for b in (2, 8, 10, 16):
        r = _convert(str(value), b)
        if b == 16:
            r = r if r else "0"
        lines.append(f"{BASE_NAMES[b]}: {r}")
    await ctx.reply("\n".join(lines))
