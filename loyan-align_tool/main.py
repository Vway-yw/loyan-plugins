"""文本对齐 — 文本左右对齐/居中

命令：
  /对齐 <文本>       — 居中显示
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("文本对齐")

# ── 常量定义 ──
MAX_LEN = 100


@on_command("/对齐", "/居中", "/center")
@plugin_handler
async def handle_align(ctx: PluginContext):
    """文本对齐"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    text = parts[1].strip() if len(parts) > 1 else ""

    if not text:
        await ctx.reply("📐 用法：/对齐 <文本>\n例：/对齐 你好世界")
        return
    if len(text) > MAX_LEN:
        await ctx.reply(f"❌ 文本过长（最多 {MAX_LEN} 字符）")
        return

    width = 20
    centered = text.center(width, " ")
    bordered = "╔" + "═" * (width + 2) + "╗\n" + "║ " + centered + " ║\n" + "╚" + "═" * (width + 2) + "╝"
    await ctx.reply(f"📐 文本对齐\n━━━━━━━━━━━━\n{bordered}")
