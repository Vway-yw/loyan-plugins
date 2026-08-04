"""大小写转换 — 文本大小写转换

命令：
  /大小写 <文本>        — 转换（自动识别）
  /大写 <文本>          — 转大写
  /小写 <文本>          — 转小写
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("大小写转换")

# ── 常量定义 ──
MAX_LEN = 1000


@on_command("/大小写", "/大写", "/小写", "/case")
@plugin_handler
async def handle_case(ctx: PluginContext):
    """大小写转换"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    text = parts[1].strip() if len(parts) > 1 else ""

    if not text:
        await ctx.reply("🔠 用法：\n/大写 <文本>\n/小写 <文本>\n/大小写 <文本> 自动转换")
        return
    if len(text) > MAX_LEN:
        await ctx.reply(f"❌ 文本过长（最多 {MAX_LEN} 字符）")
        return

    cmd = ctx.command.lstrip("/")
    if cmd == "大写":
        result = text.upper()
        label = "大写"
    elif cmd == "小写":
        result = text.lower()
        label = "小写"
    else:
        # 自动：大写字母多就转小写，否则转大写
        upper_count = sum(1 for c in text if c.isupper())
        lower_count = sum(1 for c in text if c.islower())
        if upper_count > lower_count:
            result = text.lower()
            label = "转小写"
        else:
            result = text.upper()
            label = "转大写"

    await ctx.reply(f"🔠 {label}\n━━━━━━━━━━━━\n📝 {text[:50]}\n🔑 {result[:300]}")
