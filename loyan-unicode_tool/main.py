"""Unicode 工具 — Unicode 编解码

命令：
  /unicode 编码 <文本>    — 转 Unicode 码点
  /unicode 解码 <码点>    — 码点转文本
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("Unicode工具")


def _encode(text: str) -> str:
    """文本转 Unicode 码点"""
    return " ".join(f"U+{ord(c):04X}" for c in text)


def _decode(codes: str) -> str:
    """Unicode 码点转文本"""
    result = []
    for part in codes.replace("U+", "").replace("u+", "").split():
        try:
            result.append(chr(int(part, 16)))
        except ValueError:
            result.append(part)
    return "".join(result)


@on_command("/unicode", "/unicode编码", "/unicode解码")
@plugin_handler
async def handle_unicode(ctx: PluginContext):
    """Unicode 编解码"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)

    if len(parts) < 2:
        await ctx.reply("🔤 用法：\n/unicode 编码 <文本>\n/unicode 解码 <码点>\n例：/unicode 编码 你好")
        return

    action = parts[0].lstrip("/").lower()
    text = parts[2] if len(parts) > 2 else (parts[1] if len(parts) == 2 else "")

    if not text:
        await ctx.reply("❌ 请输入内容")
        return

    if "编码" in action:
        result = _encode(text)
        label = "编码"
    elif "解码" in action:
        result = _decode(text)
        label = "解码"
    else:
        result = _encode(text)
        label = "编码"

    await ctx.reply(f"🔤 Unicode {label}\n━━━━━━━━━━━━\n📝 {text[:50]}\n🔑 {result[:500]}")
