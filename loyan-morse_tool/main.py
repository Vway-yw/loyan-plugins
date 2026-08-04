"""摩斯电码 — 文本与摩斯电码互转

命令：
  /摩斯 编码 hello     — 文本转摩斯
  /摩斯 解码 .... . .-.. .-.. ---   — 摩斯转文本
"""

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("摩斯电码")

# ── 常量定义 ──
MORSE = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
    'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
    'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
    '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
}
REVERSE = {v: k for k, v in MORSE.items()}


def _encode(text: str) -> str:
    """文本转摩斯"""
    return " ".join(MORSE.get(c.upper(), " ") for c in text.upper())


def _decode(morse: str) -> str:
    """摩斯转文本"""
    return "".join(REVERSE.get(c, " ") for c in morse.split())


@on_command("/摩斯", "/摩斯电码", "/morse")
@plugin_handler
async def handle_morse(ctx: PluginContext):
    """摩斯电码"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 2)
    if len(parts) < 3:
        await ctx.reply("📡 用法：\n/摩斯 编码 hello\n/摩斯 解码 .... . .-.. .-.. ---")
        return

    action = parts[1]
    text = parts[2] if len(parts) > 2 else ""
    if action == "编码":
        result = _encode(text)
        await ctx.reply(f"📡 摩斯编码\n━━━━━━━━━━━━\n📝 {text}\n🔑 {result[:500]}")
    elif action == "解码":
        result = _decode(text)
        await ctx.reply(f"📡 摩斯解码\n━━━━━━━━━━━━\n📝 {text[:100]}\n🔑 {result}")
    else:
        await ctx.reply("❌ 用法：/摩斯 编码|解码 <内容>")
