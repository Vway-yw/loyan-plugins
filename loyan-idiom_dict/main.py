"""成语词典 — 内置成语查询（含释义）

命令：
  /成语词典 <成语>     — 查询成语释义
"""

import json
import os

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("成语词典")

# ── 常量定义 ──
IDIOM_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "idiom.json")


def _load() -> dict:
    """加载成语库"""
    try:
        with open(IDIOM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@on_command("/成语词典", "/查成语", "/idiom")
@plugin_handler
async def handle_idiom_dict(ctx: PluginContext):
    """查询成语释义"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    word = parts[1].strip() if len(parts) > 1 else ""

    if not word:
        await ctx.reply("📖 用法：/成语词典 <成语>\n例：/成语词典 一马当先")
        return

    data = _load()
    entry = data.get(word)
    if not entry:
        # 模糊匹配
        matches = [w for w in data if word in w][:5]
        if matches:
            await ctx.reply(f"📖 未找到「{word}」，相关成语：\n{' '.join(matches)}\n💡 /成语词典 <完整成语>")
            return
        await ctx.reply(f"😢 未找到成语「{word}」")
        return

    pinyin = entry.get("p", "")
    explain = entry.get("e", "")
    lines = [f"📖 {word}", "━━━━━━━━━━━━"]
    if pinyin:
        lines.append(f"🔊 {pinyin}")
    if explain:
        lines.append(f"📌 释义: {explain[:100]}")

    await ctx.reply("\n".join(lines))
