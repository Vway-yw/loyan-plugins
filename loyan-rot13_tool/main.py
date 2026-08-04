"""ROT13 — 凯撒密码/ROT13 加密解密

命令：
  /rot13 <文本>     — ROT13 变换
  /凯撒 <偏移> <文本> — 凯撒密码
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("ROT13/凯撒")


def _rot(text: str, shift: int) -> str:
    """凯撒变换"""
    result = []
    for c in text:
        if 'a' <= c <= 'z':
            result.append(chr((ord(c) - ord('a') + shift) % 26 + ord('a')))
        elif 'A' <= c <= 'Z':
            result.append(chr((ord(c) - ord('A') + shift) % 26 + ord('A')))
        else:
            result.append(c)
    return "".join(result)


@on_command("/rot13", "/凯撒", "/caesar")
@plugin_handler
async def handle_rot(ctx: PluginContext):
    """ROT13/凯撒密码"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)

    if len(parts) < 2:
        await ctx.reply("🔐 用法：\n/rot13 <文本>\n/凯撒 <偏移> <文本>\n例：/rot13 hello")
        return

    if parts[0].lstrip("/") in ("rot13",):
        text = parts[1]
        result = _rot(text, 13)
        await ctx.reply(f"🔐 ROT13\n━━━━━━━━━━━━\n📝 {text}\n🔑 {result}")
    elif parts[0].lstrip("/") in ("凯撒", "caesar"):
        if len(parts) < 3 or not parts[1].isdigit():
            await ctx.reply("❌ 用法：/凯撒 <偏移> <文本>")
            return
        shift = int(parts[1]) % 26
        text = parts[2]
        result = _rot(text, shift)
        await ctx.reply(f"🔐 凯撒密码（偏移 {shift}）\n━━━━━━━━━━━━\n📝 {text}\n🔑 {result}")
    else:
        await ctx.reply("❌ 用法：/rot13 <文本>")
