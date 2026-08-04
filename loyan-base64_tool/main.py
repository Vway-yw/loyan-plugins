"""Base64 编解码 — 文本与 Base64 互转

命令：
  /base64 编码 <文本>    — 编码为 Base64
  /base64 解码 <文本>    — 解码 Base64
"""

import base64

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("Base64工具")

# ── 常量定义 ──
MAX_LEN = 2000


@on_command("/base64", "/b64")
@plugin_handler
async def handle_base64(ctx: PluginContext):
    """Base64 编解码"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)
    if len(parts) < 2:
        await ctx.reply("🔤 用法：\n/base64 编码 <文本>\n/base64 解码 <文本>\n例：/base64 编码 hello")
        return

    action = parts[1].strip()
    text = parts[2].strip() if len(parts) > 2 else ""

    if not text:
        await ctx.reply("❌ 请输入内容")
        return
    if len(text) > MAX_LEN:
        await ctx.reply(f"❌ 内容过长（最多 {MAX_LEN} 字符）")
        return

    try:
        if action == "编码":
            result = base64.b64encode(text.encode("utf-8")).decode("utf-8")
            await ctx.reply(f"🔤 Base64 编码\n━━━━━━━━━━━━\n📝 输入: {text[:50]}\n🔑 结果: {result}")
        elif action == "解码":
            result = base64.b64decode(text).decode("utf-8", errors="replace")
            await ctx.reply(f"🔤 Base64 解码\n━━━━━━━━━━━━\n📝 输入: {text[:50]}\n🔑 结果: {result}")
        else:
            await ctx.reply("❌ 用法：/base64 编码|解码 <内容>")
    except Exception as e:
        logger.error(f"Base64 处理失败: {e}")
        await ctx.reply("❌ 处理失败（解码内容可能不是合法 Base64）")
