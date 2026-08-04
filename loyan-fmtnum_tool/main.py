"""千分位格式化 — 数字格式化

命令：
  /千分位 1234567.89     — 千分位格式化
  /千分位 1234567 16     — 转十六进制
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("数字格式化")


@on_command("/千分位", "/格式化数字", "/formatnum")
@plugin_handler
async def handle_fmt_num(ctx: PluginContext):
    """数字格式化"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split()
    if len(parts) < 2:
        await ctx.reply("🔢 用法：/千分位 <数字>\n例：/千分位 1234567.89")
        return

    arg = parts[1]
    try:
        if "." in arg:
            num = float(arg)
            formatted = f"{num:,.2f}"
        else:
            num = int(arg)
            formatted = f"{num:,}"
    except ValueError:
        await ctx.reply("❌ 请输入数字")
        return

    lines = [f"🔢 {arg} 格式化", "━━━━━━━━━━━━"]
    lines.append(f"💲 千分位: {formatted}")
    if isinstance(num, int):
        lines.append(f"🔤 十六进制: {num:X}")
        lines.append(f"🔢 二进制: {num:b}")
    await ctx.reply("\n".join(lines))
