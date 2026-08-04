"""URL 编解码 — URL 编码/解码

命令：
  /url 编码 <文本>    — URL 编码
  /url 解码 <文本>    — URL 解码
"""

import urllib.parse

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("URL编解码")

# ── 常量定义 ──
MAX_LEN = 2000


@on_command("/url", "/url编码", "/url解码")
@plugin_handler
async def handle_url(ctx: PluginContext):
    """URL 编解码"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)

    if len(parts) < 2:
        await ctx.reply("🔗 用法：\n/url 编码 <文本>\n/url 解码 <文本>\n例：/url 编码 你好 world")
        return

    action = parts[0].lstrip("/").lower()
    text = parts[2] if len(parts) > 2 else (parts[1] if len(parts) == 2 else "")

    if not text:
        await ctx.reply("❌ 请输入内容")
        return
    if len(text) > MAX_LEN:
        await ctx.reply(f"❌ 内容过长")
        return

    if "编码" in action or action == "url":
        result = urllib.parse.quote(text)
        label = "编码"
    elif "解码" in action:
        result = urllib.parse.unquote(text)
        label = "解码"
    else:
        await ctx.reply("❌ 用法：/url 编码|解码 <内容>")
        return

    await ctx.reply(f"🔗 URL {label}\n━━━━━━━━━━━━\n📝 {text[:50]}\n🔑 {result[:500]}")
