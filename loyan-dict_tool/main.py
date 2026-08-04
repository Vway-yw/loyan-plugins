"""英语词典 — 查询英文单词释义（免费）

命令：
  /词典 <单词>     — 查询单词释义
  /dict <word>     — 同 /词典
"""

import asyncio
import json
import time
import urllib.parse
import urllib.request
from typing import Optional

from graci import on_command, plugin_handler, PluginContext, get_logger

logger = get_logger("英语词典")

# ── 常量定义 ──
API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
TIMEOUT = 15
CACHE_TTL = 3600

# ── 模块级状态 ──
_cache: dict = {}


def _fetch(word: str) -> Optional[list]:
    """查询单词"""
    url = API_URL.format(word=urllib.parse.quote(word))
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


@on_command("/词典", "/dict", "/英语词典")
@plugin_handler
async def handle_dict(ctx: PluginContext):
    """查询英文单词"""
    rest = (ctx.raw_text or "").strip()
    parts = rest.split(None, 1)
    word = parts[1].strip() if len(parts) > 1 else ""

    if not word:
        await ctx.reply("📖 用法：/词典 <单词>\n例：/词典 hello")
        return
    if not word.replace(" ", "").isalpha():
        await ctx.reply("❌ 请输入英文字母")
        return

    now = time.time()
    cached = _cache.get(word)
    if cached and now - cached[0] < CACHE_TTL:
        data = cached[1]
    else:
        try:
            data = await asyncio.to_thread(_fetch, word)
            if data:
                _cache[word] = (now, data)
        except Exception as e:
            logger.error(f"词典查询失败: {e}")
            data = None

    if not data:
        await ctx.reply(f"😢 未找到单词「{word}」或查询失败")
        return

    lines = [f"📖 {word}", "━━━━━━━━━━━━"]
    for entry in data[:2]:
        phonetics = [p.get("text", "") for p in entry.get("phonetics", []) if p.get("text")]
        if phonetics:
            lines.append(f"🔊 音标: {phonetics[0]}")
        for meaning in entry.get("meanings", [])[:3]:
            pos = meaning.get("partOfSpeech", "")
            for defn in meaning.get("definitions", [])[:2]:
                lines.append(f"📌 [{pos}] {defn.get('definition', '')}")
                if defn.get("example"):
                    lines.append(f"   📝 例: {defn['example']}")
    await ctx.reply("\n".join(lines[:15]))
