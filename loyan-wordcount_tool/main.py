"""字数统计 — 统计文本字数/字符数/行数

命令：
  /字数 <文本>      — 统计文本
  /wc <文本>        — 同 /字数
"""

import re

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("字数统计")

# ── 常量定义 ──
MAX_LEN = 5000


@on_command("/字数", "/统计", "/wc")
@plugin_handler
async def handle_wordcount(ctx: PluginContext):
    """统计字数"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    text = parts[1].strip() if len(parts) > 1 else ""

    if not text:
        await ctx.reply("📊 用法：/字数 <文本>\n例：/字数 你好世界 hello")
        return
    if len(text) > MAX_LEN:
        await ctx.reply(f"❌ 文本过长（最多 {MAX_LEN} 字符）")
        return

    total_chars = len(text)
    # 中文字符（含标点）
    cjk = len(re.findall(r"[\u4e00-\u9fa5]", text))
    # 中文字符+标点
    cjk_punct = len(re.findall(r"[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]", text))
    # 英文字母
    letters = len(re.findall(r"[a-zA-Z]", text))
    # 数字
    digits = len(re.findall(r"\d", text))
    # 空格
    spaces = text.count(" ")
    # 单词数（英文）
    words = len(re.findall(r"[a-zA-Z]+", text))
    # 行数
    lines = text.count("\n") + 1

    await ctx.reply(
        f"📊 字数统计\n"
        f"━━━━━━━━━━━━\n"
        f"🔤 总字符: {total_chars}\n"
        f"🀄 中文字符: {cjk}\n"
        f"📝 中文含标点: {cjk_punct}\n"
        f"🔡 英文字母: {letters}\n"
        f"🔢 数字: {digits}\n"
        f"🔠 英文单词: {words}\n"
        f"␣ 空格: {spaces}\n"
        f"📄 行数: {lines}"
    )
