"""文本反转 — 文本反转/倒序/翻转

命令：
  /反转 <文本>       — 反转文本
  /倒序 <文本>       — 倒序
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("文本反转")

# ── 常量定义 ──
MAX_LEN = 500


@on_command("/反转", "/倒序", "/reverse")
@plugin_handler
async def handle_reverse(ctx: PluginContext):
    """文本反转"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    text = parts[1].strip() if len(parts) > 1 else ""

    if not text:
        await ctx.reply("🔁 用法：/反转 <文本>\n例：/反转 hello world")
        return
    if len(text) > MAX_LEN:
        await ctx.reply(f"❌ 文本过长（最多 {MAX_LEN} 字符）")
        return

    reversed_text = text[::-1]
    await ctx.reply(f"🔁 文本反转\n━━━━━━━━━━━━\n📝 {text}\n🔑 {reversed_text}")
